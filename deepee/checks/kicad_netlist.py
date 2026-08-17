from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Dict, List, Optional

from .common import command_available, resolve_run_path, result, run_subprocess


def _first_file(root: Path, suffix: str) -> Optional[Path]:
    matches = sorted(root.glob(f"**/*{suffix}"))
    return matches[0] if matches else None


def _match(actual: str, expected: Any) -> bool:
    if isinstance(expected, dict) and "pattern" in expected:
        return re.fullmatch(str(expected["pattern"]), actual, re.IGNORECASE) is not None
    return actual == str(expected)


def _normalize_top_level_net_name(name: str) -> str:
    """Match KiCad's XML spelling for root-sheet local labels.

    KiCad 10 prefixes root-sheet local labels with a single slash in the XML
    netlist (for example, ``/SDA``), while global and power labels remain
    unprefixed.  Preserve hierarchical names such as ``/Sensor/SDA``.
    """
    return name[1:] if name.startswith("/") and "/" not in name[1:] else name


def run_kicad_netlist_contract(check: Dict[str, Any], task, run_dir: Path, options: Dict[str, Any]) -> Dict[str, Any]:
    root = resolve_run_path(run_dir, str(check.get("root", "artifacts")))
    schematic = resolve_run_path(run_dir, str(check["schematic"])) if check.get("schematic") else _first_file(root, ".kicad_sch")
    if not schematic or not schematic.is_file():
        return result(check.get("name", "kicad_netlist_contract"), "kicad_netlist_contract", 0.0, "No KiCad schematic found", required_failed=True)
    if not command_available("kicad-cli"):
        skipped = bool(options.get("allow_missing_tools"))
        return result(
            check.get("name", "kicad_netlist_contract"),
            "kicad_netlist_contract",
            0.0,
            "kicad-cli not available",
            {"schematic": str(schematic)},
            required_failed=not skipped,
            skipped=skipped,
        )

    work_dir = Path(options.get("work_dir") or (run_dir / ".deepee" / "verification"))
    output = work_dir / f"{task.id}-netlist.xml"
    output.parent.mkdir(parents=True, exist_ok=True)
    command = [
        "kicad-cli",
        "sch",
        "export",
        "netlist",
        "--format",
        "kicadxml",
        "--output",
        str(output),
        str(schematic),
    ]
    proc = run_subprocess(command, run_dir, int(check.get("timeout_seconds", 120)))
    if proc["returncode"] != 0 or not output.is_file():
        return result(
            check.get("name", "kicad_netlist_contract"),
            "kicad_netlist_contract",
            0.0,
            "KiCad netlist export failed",
            {"command": command, "run": proc},
            required_failed=True,
        )

    try:
        document = ET.parse(output).getroot()
    except (OSError, ET.ParseError) as exc:
        return result(check.get("name", "kicad_netlist_contract"), "kicad_netlist_contract", 0.0, f"Invalid KiCad XML netlist: {exc}", required_failed=True)

    components: Dict[str, Dict[str, str]] = {}
    for component in document.findall("./components/comp"):
        reference = component.get("ref") or ""
        libsource = component.find("libsource")
        components[reference] = {
            "value": component.findtext("value") or "",
            "footprint": component.findtext("footprint") or "",
            "library": (libsource.get("lib") if libsource is not None else "") or "",
        }

    pin_nets: Dict[str, str] = {}
    nets: Dict[str, List[str]] = {}
    for net in document.findall("./nets/net"):
        net_name = _normalize_top_level_net_name(net.get("name") or "")
        members = []
        for node in net.findall("node"):
            key = f"{node.get('ref', '')}.{node.get('pin', '')}"
            pin_nets[key] = net_name
            members.append(key)
        nets[net_name] = sorted(members)

    subchecks: List[Dict[str, Any]] = []
    expected_refs = set()
    for expected in check.get("components") or []:
        reference = str(expected["reference"])
        expected_refs.add(reference)
        actual = components.get(reference)
        passed = actual is not None
        mismatches = {}
        if actual:
            for field in ("value", "footprint"):
                if field in expected and not _match(actual[field], expected[field]):
                    passed = False
                    mismatches[field] = {"expected": expected[field], "actual": actual[field]}
        subchecks.append({"name": f"component:{reference}", "passed": passed, "actual": actual, "mismatches": mismatches})

    if check.get("exact_references"):
        actual_refs = {reference for reference in components if reference and not reference.startswith("#")}
        subchecks.append({
            "name": "exact_references",
            "passed": actual_refs == expected_refs,
            "expected": sorted(expected_refs),
            "actual": sorted(actual_refs),
        })

    for pin, expected_net in (check.get("pin_nets") or {}).items():
        actual_net = pin_nets.get(str(pin))
        subchecks.append({
            "name": f"pin_net:{pin}",
            "passed": actual_net is not None and _match(actual_net, expected_net),
            "expected": expected_net,
            "actual": actual_net,
        })

    passed_count = sum(1 for item in subchecks if item["passed"])
    score = passed_count / len(subchecks) if subchecks else 1.0
    return result(
        check.get("name", "kicad_netlist_contract"),
        "kicad_netlist_contract",
        score,
        f"Passed {passed_count}/{len(subchecks)} netlist contract checks",
        {"command": command, "components": components, "nets": nets, "subchecks": subchecks},
        required_failed=score < 1.0,
    )
