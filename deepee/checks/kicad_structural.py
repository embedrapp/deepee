from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

from .common import resolve_run_path, result
from .sexpr import SExpressionError, atom, child, children, find, head, parse, property_value


def _xy(node: Optional[List[Any]]) -> Optional[Tuple[float, float]]:
    if not node or len(node) < 3:
        return None
    try:
        return float(atom(node, 1)), float(atom(node, 2))
    except ValueError:
        return None


def _outline_dimensions(design: List[Any]) -> Optional[Dict[str, float]]:
    points: List[Tuple[float, float]] = []
    for item in design[1:]:
        if not isinstance(item, list) or head(item) not in {"gr_arc", "gr_circle", "gr_line", "gr_rect"}:
            continue
        if atom(child(item, "layer")) != "Edge.Cuts":
            continue
        for coordinate_name in ("start", "end", "mid", "center"):
            point = _xy(child(item, coordinate_name))
            if point:
                points.append(point)
    if not points:
        return None
    xs = [point[0] for point in points]
    ys = [point[1] for point in points]
    return {
        "width_mm": round(max(xs) - min(xs), 4),
        "height_mm": round(max(ys) - min(ys), 4),
        "min_x": round(min(xs), 4),
        "max_x": round(max(xs), 4),
        "min_y": round(min(ys), 4),
        "max_y": round(max(ys), 4),
    }


def _first_file(root: Path, suffix: str) -> Optional[Path]:
    matches = sorted(root.glob(f"**/*{suffix}"))
    return matches[0] if matches else None


def _load_design(path: Path, expected_root: str, min_bytes: int) -> Tuple[Optional[List[Any]], Optional[str]]:
    try:
        if path.stat().st_size < min_bytes:
            return None, f"File is smaller than {min_bytes} bytes"
        root = parse(path.read_text(encoding="utf-8", errors="strict"))
    except (OSError, UnicodeError, SExpressionError) as exc:
        return None, f"Cannot parse KiCad S-expression: {exc}"
    if head(root) != expected_root:
        return None, f"Expected ({expected_root} ...) root"
    return root, None


def _role_results(values: Iterable[str], requirements: Iterable[Any]) -> List[Dict[str, Any]]:
    searchable = [value for value in values if value]
    results = []
    for requirement in requirements:
        if isinstance(requirement, str):
            requirement = {"name": requirement, "patterns": [requirement]}
        name = str(requirement.get("name") or "component")
        patterns = requirement.get("patterns") or [requirement.get("pattern")]
        matched = None
        for value in searchable:
            if any(pattern and re.search(str(pattern), value, re.IGNORECASE) for pattern in patterns):
                matched = value
                break
        results.append({"name": name, "passed": matched is not None, "matched": matched})
    return results


def _pattern_results(values: Iterable[str], patterns: Iterable[str], label: str) -> List[Dict[str, Any]]:
    searchable = [value for value in values if value]
    results = []
    for pattern in patterns:
        matched = next((value for value in searchable if re.search(str(pattern), value, re.IGNORECASE)), None)
        results.append({"name": f"{label}:{pattern}", "passed": matched is not None, "matched": matched})
    return results


def _component_contract_results(
    records: Dict[str, Dict[str, str]],
    contracts: Iterable[Dict[str, Any]],
    exact_references: bool,
) -> List[Dict[str, Any]]:
    results: List[Dict[str, Any]] = []
    expected_refs = set()
    for contract in contracts:
        reference = str(contract.get("reference") or "")
        expected_refs.add(reference)
        actual = records.get(reference)
        mismatches = {}
        passed = actual is not None
        if actual:
            for field in ("value", "footprint", "library"):
                if field in contract and actual.get(field, "") != str(contract[field]):
                    mismatches[field] = {"expected": str(contract[field]), "actual": actual.get(field, "")}
                    passed = False
        results.append({"name": f"component:{reference}", "passed": passed, "actual": actual, "mismatches": mismatches})
    if exact_references:
        actual_refs = {reference for reference in records if reference and not reference.startswith("#")}
        results.append({
            "name": "exact_references",
            "passed": actual_refs == expected_refs,
            "expected": sorted(expected_refs),
            "actual": sorted(actual_refs),
        })
    return results


def _finish(check: Dict[str, Any], check_type: str, checks: List[Dict[str, Any]], details: Dict[str, Any]) -> Dict[str, Any]:
    passed_count = sum(1 for item in checks if item["passed"])
    score = passed_count / len(checks) if checks else 1.0
    details["subchecks"] = checks
    return result(
        check.get("name", check_type),
        check_type,
        score,
        f"Passed {passed_count}/{len(checks)} structural checks",
        details,
        required_failed=bool(check.get("required", True) and score < 1.0),
    )


def run_kicad_schematic_structure(check: Dict[str, Any], task, run_dir: Path, options: Dict[str, Any]) -> Dict[str, Any]:
    root_dir = resolve_run_path(run_dir, str(check.get("root", "artifacts")))
    schematic = resolve_run_path(run_dir, str(check["schematic"])) if check.get("schematic") else _first_file(root_dir, ".kicad_sch")
    if not schematic or not schematic.is_file():
        return result(check.get("name", "kicad_schematic_structure"), "kicad_schematic_structure", 0.0, "No KiCad schematic found", required_failed=check.get("required", True))

    design, error = _load_design(schematic, "kicad_sch", int(check.get("min_bytes", 1000)))
    if not design:
        return result(check.get("name", "kicad_schematic_structure"), "kicad_schematic_structure", 0.0, error or "Invalid schematic", {"schematic": str(schematic.relative_to(run_dir))}, required_failed=check.get("required", True))

    symbols = [item for item in design[1:] if isinstance(item, list) and head(item) == "symbol" and child(item, "lib_id")]
    wires = [item for item in design[1:] if isinstance(item, list) and head(item) == "wire"]
    labels = [item for item in design[1:] if isinstance(item, list) and head(item) in {"label", "global_label", "hierarchical_label"}]
    symbol_values = []
    references = []
    component_records: Dict[str, Dict[str, str]] = {}
    for symbol in symbols:
        lib_id = atom(child(symbol, "lib_id"))
        value = property_value(symbol, "Value")
        reference = property_value(symbol, "Reference")
        footprint = property_value(symbol, "Footprint")
        symbol_values.append(" ".join(part for part in (lib_id, value, reference) if part))
        references.append(reference)
        if reference:
            component_records[reference] = {
                "value": value,
                "footprint": footprint,
                "library": lib_id,
            }

    power_values = [
        property_value(symbol, "Value") or atom(child(symbol, "lib_id"))
        for symbol in symbols
        if atom(child(symbol, "lib_id")).lower().startswith("power:")
    ]
    net_names = [atom(label) for label in labels] + power_values
    duplicate_refs = sorted({ref for ref in references if ref and references.count(ref) > 1})

    subchecks = [
        {"name": "minimum_symbols", "passed": len(symbols) >= int(check.get("min_symbols", 1)), "actual": len(symbols)},
        {"name": "minimum_wires", "passed": len(wires) >= int(check.get("min_wires", 1)), "actual": len(wires)},
        {"name": "unique_references", "passed": not duplicate_refs, "duplicates": duplicate_refs},
    ]
    subchecks.extend(_role_results(symbol_values, check.get("required_components") or []))
    subchecks.extend(_component_contract_results(
        component_records,
        check.get("components") or [],
        bool(check.get("exact_references")),
    ))
    subchecks.extend(_pattern_results(net_names, check.get("required_nets") or [], "net"))
    return _finish(
        check,
        "kicad_schematic_structure",
        subchecks,
        {
            "schematic": str(schematic.relative_to(run_dir.resolve())),
            "symbol_count": len(symbols),
            "wire_count": len(wires),
            "labels": sorted(set(net_names)),
            "components": component_records,
        },
    )


def _net_name(node: List[Any], legacy_nets: Dict[str, str]) -> str:
    net = child(node, "net")
    if not net:
        return ""
    # KiCad 9 and earlier serialize ``(net 1 "GND")`` and define a
    # top-level net table.  KiCad 10 serializes ``(net "GND")`` directly on
    # pads and copper items and omits that table.
    return atom(net, 2) or legacy_nets.get(atom(net, 1), atom(net, 1))


def run_kicad_pcb_structure(check: Dict[str, Any], task, run_dir: Path, options: Dict[str, Any]) -> Dict[str, Any]:
    root_dir = resolve_run_path(run_dir, str(check.get("root", "artifacts")))
    board = resolve_run_path(run_dir, str(check["board"])) if check.get("board") else _first_file(root_dir, ".kicad_pcb")
    if not board or not board.is_file():
        return result(check.get("name", "kicad_pcb_structure"), "kicad_pcb_structure", 0.0, "No KiCad PCB found", required_failed=check.get("required", True))

    design, error = _load_design(board, "kicad_pcb", int(check.get("min_bytes", 1000)))
    if not design:
        return result(check.get("name", "kicad_pcb_structure"), "kicad_pcb_structure", 0.0, error or "Invalid board", {"board": str(board.relative_to(run_dir))}, required_failed=check.get("required", True))

    footprints = children(design, "footprint")
    segments = children(design, "segment")
    vias = children(design, "via")
    zones = children(design, "zone")
    nets = {atom(item, 1): atom(item, 2) for item in children(design, "net")}
    layers_node = child(design, "layers") or []
    copper_layers = [atom(item, 1) for item in layers_node[1:] if isinstance(item, list) and atom(item, 1).endswith(".Cu")]

    footprint_values = []
    component_records: Dict[str, Dict[str, str]] = {}
    pad_nets: Dict[str, int] = {}
    pin_nets: Dict[str, str] = {}
    mounting_holes = 0
    for footprint in footprints:
        library = atom(footprint, 1)
        reference = property_value(footprint, "Reference")
        value = property_value(footprint, "Value")
        footprint_values.append(" ".join(filter(None, [library, reference, value])))
        if reference:
            component_records[reference] = {"value": value, "footprint": library, "library": library}
        for pad in find(footprint, "pad"):
            if len(pad) > 2 and atom(pad, 2) == "np_thru_hole":
                mounting_holes += 1
            pad_net = child(pad, "net")
            if pad_net:
                name = _net_name(pad, nets)
                if name:
                    pad_nets[name] = pad_nets.get(name, 0) + 1
                    if reference:
                        pin_nets[f"{reference}.{atom(pad, 1)}"] = name

    routed_names = {_net_name(item, nets) for item in segments + vias if _net_name(item, nets)}
    zone_names = {atom(child(zone, "net_name")) or _net_name(zone, nets) for zone in zones}
    route_evidence = routed_names | zone_names
    net_names = set(nets.values()) | set(pad_nets) | route_evidence
    keepouts = [zone for zone in zones if child(zone, "keepout")]
    dimensions = _outline_dimensions(design)

    subchecks = [
        {"name": "copper_layer_count", "passed": len(copper_layers) == int(check.get("copper_layers", 2)), "actual": copper_layers},
        {"name": "minimum_footprints", "passed": len(footprints) >= int(check.get("min_footprints", 1)), "actual": len(footprints)},
        {"name": "minimum_tracks", "passed": len(segments) >= int(check.get("min_tracks", 1)), "actual": len(segments)},
        {"name": "mounting_holes", "passed": mounting_holes >= int(check.get("min_mounting_holes", 0)), "actual": mounting_holes},
    ]
    if check.get("expected_width_mm") is not None or check.get("expected_height_mm") is not None:
        tolerance = float(check.get("tolerance_mm", 0.5))
        expected_width = float(check.get("expected_width_mm"))
        expected_height = float(check.get("expected_height_mm"))
        subchecks.append({"name": "board_width", "passed": bool(dimensions and abs(dimensions["width_mm"] - expected_width) <= tolerance), "actual": dimensions["width_mm"] if dimensions else None})
        subchecks.append({"name": "board_height", "passed": bool(dimensions and abs(dimensions["height_mm"] - expected_height) <= tolerance), "actual": dimensions["height_mm"] if dimensions else None})
    if check.get("require_keepout"):
        subchecks.append({"name": "copper_keepout", "passed": bool(keepouts), "actual": len(keepouts)})
    if check.get("require_ground_zone"):
        subchecks.append({"name": "ground_zone", "passed": any(re.search(r"^(GND|0V)$", name, re.IGNORECASE) for name in zone_names), "actual": sorted(zone_names)})

    subchecks.extend(_role_results(footprint_values, check.get("required_components") or []))
    subchecks.extend(_component_contract_results(
        component_records,
        check.get("components") or [],
        bool(check.get("exact_references")),
    ))
    for pin, expected_net in (check.get("pin_nets") or {}).items():
        actual_net = pin_nets.get(str(pin))
        subchecks.append({
            "name": f"pin_net:{pin}",
            "passed": actual_net == str(expected_net),
            "expected": str(expected_net),
            "actual": actual_net,
        })
    for pattern in check.get("required_routed_nets") or []:
        matching_nets = [name for name in net_names if re.search(str(pattern), name, re.IGNORECASE)]
        has_pad = any(name in pad_nets for name in matching_nets)
        has_route = any(name in route_evidence for name in matching_nets)
        subchecks.append({"name": f"routed_net:{pattern}", "passed": bool(matching_nets and has_pad and has_route), "matched": matching_nets, "has_pad": has_pad, "has_route": has_route})

    return _finish(
        check,
        "kicad_pcb_structure",
        subchecks,
        {
            "board": str(board.relative_to(run_dir.resolve())),
            "dimensions": dimensions,
            "footprint_count": len(footprints),
            "segment_count": len(segments),
            "via_count": len(vias),
            "net_count": len(net_names),
            "routed_nets": sorted(route_evidence),
            "components": component_records,
            "pin_nets": pin_nets,
        },
    )
