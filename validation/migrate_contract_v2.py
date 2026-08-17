from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, Tuple

import yaml


ROOT = Path(__file__).resolve().parents[1]

CHECK_REQUIREMENTS: Dict[str, Tuple[str, str]] = {
    "artifact_presence": ("deliverable", "Produce every required submission artifact."),
    "starter_integrity": ("integrity", "Preserve the declared protected starter interface and project files."),
    "c_unit_tests": ("behavior", "Satisfy the verifier-owned behavioral and boundary test vectors."),
    "firmware_build": ("build", "Build the submitted firmware for the declared target without errors."),
    "kicad_schematic_structure": ("logical", "Satisfy the declared native schematic component and net contract."),
    "kicad_netlist_contract": ("logical", "Satisfy the independently exported electrical netlist contract."),
    "kicad_erc": ("electrical", "Pass KiCad electrical-rules checking without errors or warnings."),
    "kicad_pcb_structure": ("physical", "Satisfy the declared native PCB structure and routing contract."),
    "kicad_drc": ("manufacturability", "Pass KiCad design-rules checking without errors or warnings."),
}


def stable_id(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def migrate(path: Path) -> bool:
    text = path.read_text(encoding="utf-8")
    manifest = yaml.safe_load(text)
    if str(manifest.get("contract_version") or "") == "2.0":
        return False

    requirements = []
    for check in manifest.get("checks") or []:
        check_type = str(check["type"])
        check_name = str(check.get("name") or check_type)
        layer, description = CHECK_REQUIREMENTS[check_type]
        requirements.append({
            "id": stable_id(check_name),
            "description": description,
            "layer": layer,
            "critical": True,
            "check": check_name,
        })

    lines = text.splitlines()
    insert_at = next(index for index, line in enumerate(lines) if line == "checks:")
    contract_lines = ["contract_version: '2.0'", "requirements:"]
    for requirement in requirements:
        contract_lines.extend([
            f"- id: {requirement['id']}",
            f"  description: {requirement['description']}",
            f"  layer: {requirement['layer']}",
            "  critical: true",
            f"  check: {requirement['check']}",
        ])
    lines[insert_at:insert_at] = contract_lines
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return True


def main() -> int:
    changed = 0
    for path in sorted((ROOT / "tasks").glob("*/*/manifest.yaml")):
        changed += int(migrate(path))
    print(f"Migrated {changed} manifest(s) to contract v2")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
