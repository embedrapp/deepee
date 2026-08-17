from __future__ import annotations

from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
MINIMUM_TRACK_WIDTH_MM = 0.25


def migrate_manifest(path: Path) -> bool:
    text = path.read_text(encoding="utf-8")
    if "track_width_constraints:" in text:
        lines = text.splitlines()
        start = next(index for index, line in enumerate(lines) if line.strip() == "track_width_constraints:")
        end = next(index for index in range(start + 1, len(lines)) if lines[index].strip() == "- type: kicad_drc")
        field_indent = lines[start][:len(lines[start]) - len(lines[start].lstrip())]
        check_indent = field_indent[:-2]
        minimum_index = next(index for index in range(start + 1, end) if lines[index].strip().startswith("minimum_mm:"))
        nets_index = next(index for index in range(start + 1, minimum_index) if lines[index].strip() == "nets:")
        nets = [
            line.strip()[2:]
            for line in lines[nets_index + 1:minimum_index]
            if line.strip().startswith("- ")
        ]
        replacement = [
            f"{field_indent}track_width_constraints:",
            f"{field_indent}  - name: all-required-nets",
            f"{field_indent}    nets:",
            *(f"{field_indent}      - {net}" for net in nets),
            f"{field_indent}    minimum_mm: {MINIMUM_TRACK_WIDTH_MM}",
        ]
        if path.parent.name == "deepee-pcb-007":
            replacement.extend([
                f"{field_indent}matched_length_groups:",
                f"{field_indent}  - name: usb2-data-pair",
                f"{field_indent}    nets:",
                f"{field_indent}      - USB_DP",
                f"{field_indent}      - USB_DM",
                f"{field_indent}    maximum_skew_mm: 1.0",
            ])
        replacement.append(f"{check_indent}- type: kicad_drc")
        normalized = lines[:start] + replacement + lines[end + 1:]
        updated = "\n".join(normalized) + "\n"
        if updated != text:
            path.write_text(updated, encoding="utf-8")
            return True
        return False

    manifest = yaml.safe_load(text)
    structure = next(
        check for check in manifest["checks"] if check["type"] == "kicad_pcb_structure"
    )
    if structure.get("track_width_constraints"):
        return False
    lines = text.splitlines()
    drc_index = next(
        (index for index, line in enumerate(lines) if line.strip() == "- type: kicad_drc"),
        None,
    )
    if drc_index is None:
        raise RuntimeError(f"Cannot find PCB DRC check boundary in {path}")
    check_indent = lines[drc_index][:len(lines[drc_index]) - len(lines[drc_index].lstrip())]
    field_indent = check_indent + "  "
    nets = structure.get("required_routed_nets") or []
    addition = [
        f"{field_indent}track_width_constraints:",
        f"{field_indent}  - name: all-required-nets",
        f"{field_indent}    nets:",
    ]
    addition.extend(f"{field_indent}      - {net}" for net in nets)
    addition.append(f"{field_indent}    minimum_mm: {MINIMUM_TRACK_WIDTH_MM}")
    if manifest["id"] == "deepee-pcb-007":
        addition.extend([
            f"{field_indent}matched_length_groups:",
            f"{field_indent}  - name: usb2-data-pair",
            f"{field_indent}    nets:",
            f"{field_indent}      - USB_DP",
            f"{field_indent}      - USB_DM",
            f"{field_indent}    maximum_skew_mm: 1.0",
        ])
    lines[drc_index:drc_index] = addition
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return True


def migrate_prompt(path: Path, matched_pair: bool) -> bool:
    text = path.read_text(encoding="utf-8")
    sentence = "Use routed copper at least 0.25 mm wide on every named net."
    if sentence in text:
        return False
    addition = "\n\n" + sentence
    if matched_pair:
        addition += " Keep the total routed lengths of `USB_DP` and `USB_DM` within 1.0 mm of each other."
    path.write_text(text.rstrip() + addition + "\n", encoding="utf-8")
    return True


def main() -> int:
    changed = 0
    for path in sorted((ROOT / "tasks").glob("*/*/manifest.yaml")):
        if path.parent.parent.name not in {"pcb", "pcb-design"}:
            continue
        changed += int(migrate_manifest(path))
        changed += int(migrate_prompt(path.parent / "prompt.md", path.parent.name == "deepee-pcb-007"))
    print(f"Updated {changed} PCB manifest/prompt file(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
