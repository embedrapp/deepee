#!/usr/bin/env python3
"""Regenerate the verifier-only reference artifacts for the four KiCad tasks."""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOLUTIONS = ROOT / "validation" / "solutions"


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def generate_repaired_schematic() -> None:
    source = ROOT / "tasks/schematic/deepee-sch-001/starter/artifacts/power-input.kicad_sch"
    destination = SOLUTIONS / "deepee-sch-001/artifacts/power-input.kicad_sch"
    text = source.read_text(encoding="utf-8")
    marker = "\n\t\t(mirror y)"
    if text.count(marker) != 1:
        raise RuntimeError("Expected exactly one mirrored starter symbol")
    _write(destination, text.replace(marker, "", 1))


def generate_completed_adapter() -> None:
    source = ROOT / "tasks/pcb/deepee-pcb-001/starter/artifacts/nrf24-adapter.kicad_pcb"
    destination = SOLUTIONS / "deepee-pcb-001/artifacts/nrf24-adapter.kicad_pcb"
    text = source.read_text(encoding="utf-8")
    if text.count("\n)") != 1:
        raise RuntimeError("Unexpected adapter board root")
    routes = """
  (segment (start 103 112.16) (end 122 109.08) (width 0.25) (layer "F.Cu") (net 5))
  (segment (start 103 114.7) (end 124.54 109.08) (width 0.25) (layer "B.Cu") (net 6))
  (segment (start 103 117.24) (end 122 111.62) (width 0.25) (layer "F.Cu") (net 7))
  (segment (start 103 119.78) (end 124.54 111.62) (width 0.25) (layer "B.Cu") (net 8))
"""
    _write(destination, text[:-2] + routes + ")\n")


def generate_breakout_schematic() -> None:
    try:
        import kicad_sch_api as ksa
    except ImportError as exc:
        raise RuntimeError(
            "Install validation/requirements.txt and set KICAD_SYMBOL_DIR to regenerate the schematic"
        ) from exc

    destination = SOLUTIONS / "deepee-sch-002/artifacts/mcp9808-breakout.kicad_sch"
    destination.parent.mkdir(parents=True, exist_ok=True)
    schematic = ksa.create_schematic("mcp9808-breakout")
    components = [
        (
            "Sensor_Temperature:MCP9808_MSOP",
            "U1",
            "MCP9808T-E/MS",
            (100, 100),
            "Package_SO:MSOP-8_3x3mm_P0.65mm",
        ),
        ("Device:R", "R1", "4.7k", (130, 80), "Resistor_SMD:R_0603_1608Metric"),
        ("Device:R", "R2", "4.7k", (145, 80), "Resistor_SMD:R_0603_1608Metric"),
        ("Device:R", "R3", "10k", (160, 80), "Resistor_SMD:R_0603_1608Metric"),
        ("Device:C", "C1", "100nF", (80, 100), "Capacitor_SMD:C_0603_1608Metric"),
        (
            "Connector_Generic:Conn_01x05",
            "J1",
            "Conn_01x05",
            (190, 100),
            "Connector_PinHeader_2.54mm:PinHeader_1x05_P2.54mm_Vertical",
        ),
        ("power:PWR_FLAG", "#FLG01", "PWR_FLAG", (70, 70), ""),
        ("power:PWR_FLAG", "#FLG02", "PWR_FLAG", (70, 130), ""),
    ]
    for library, reference, value, position, footprint in components:
        schematic.components.add(
            library,
            reference,
            value,
            position=position,
            footprint=footprint,
        )

    contract = {
        "U1": {"1": "SDA", "2": "SCL", "3": "ALERT", "4": "GND", "5": "GND", "6": "GND", "7": "GND", "8": "3V3"},
        "R1": {"1": "3V3", "2": "SDA"},
        "R2": {"1": "3V3", "2": "SCL"},
        "R3": {"1": "3V3", "2": "ALERT"},
        "C1": {"1": "3V3", "2": "GND"},
        "J1": {"1": "3V3", "2": "GND", "3": "SDA", "4": "SCL", "5": "ALERT"},
        "#FLG01": {"1": "3V3"},
        "#FLG02": {"1": "GND"},
    }
    for reference, pins in contract.items():
        for pin, net in pins.items():
            schematic.add_label(net, pin=(reference, pin))
    schematic.save(destination)


def _property(name: str, value: str, y: float) -> str:
    return f'''    (property "{name}" "{value}"
      (at 0 {y} 0)
      (layer "F.Fab")
      (effects (font (size 0.8 0.8) (thickness 0.12)))
    )'''


def _pad(number: str, kind: str, shape: str, x: float, y: float, size: str, layers: str, net: int, name: str, drill: str = "") -> str:
    drill_line = f" (drill {drill})" if drill else ""
    return (
        f'    (pad "{number}" {kind} {shape} (at {x} {y}) (size {size})'
        f'{drill_line} (layers {layers}) (net {net} "{name}"))'
    )


def _footprint(library: str, reference: str, value: str, x: float, y: float, pads: list[str]) -> str:
    return "\n".join(
        [
            f'  (footprint "{library}"',
            '    (layer "F.Cu")',
            f"    (at {x} {y})",
            _property("Reference", reference, -2),
            _property("Value", value, 2),
            *pads,
            "  )",
        ]
    )


def generate_breakout_board() -> None:
    u1_pads = [
        _pad("1", "smd", "rect", -2.1125, -0.975, "1.625 0.4", '"F.Cu" "F.Mask" "F.Paste"', 3, "SDA"),
        _pad("2", "smd", "rect", -2.1125, -0.325, "1.625 0.4", '"F.Cu" "F.Mask" "F.Paste"', 4, "SCL"),
        _pad("3", "smd", "rect", -2.1125, 0.325, "1.625 0.4", '"F.Cu" "F.Mask" "F.Paste"', 5, "ALERT"),
        _pad("4", "smd", "rect", -2.1125, 0.975, "1.625 0.4", '"F.Cu" "F.Mask" "F.Paste"', 1, "GND"),
        _pad("5", "smd", "rect", 2.1125, 0.975, "1.625 0.4", '"F.Cu" "F.Mask" "F.Paste"', 1, "GND"),
        _pad("6", "smd", "rect", 2.1125, 0.325, "1.625 0.4", '"F.Cu" "F.Mask" "F.Paste"', 1, "GND"),
        _pad("7", "smd", "rect", 2.1125, -0.325, "1.625 0.4", '"F.Cu" "F.Mask" "F.Paste"', 1, "GND"),
        _pad("8", "smd", "rect", 2.1125, -0.975, "1.625 0.4", '"F.Cu" "F.Mask" "F.Paste"', 2, "3V3"),
    ]

    def two_pad(reference: str, value: str, x: float, net1: tuple[int, str], net2: tuple[int, str], capacitor: bool = False) -> str:
        library = "Capacitor_SMD:C_0603_1608Metric" if capacitor else "Resistor_SMD:R_0603_1608Metric"
        offset = 0.775 if capacitor else 0.825
        pads = [
            _pad("1", "smd", "rect", -offset, 0, "0.9 0.95" if capacitor else "0.8 0.95", '"F.Cu" "F.Mask" "F.Paste"', *net1),
            _pad("2", "smd", "rect", offset, 0, "0.9 0.95" if capacitor else "0.8 0.95", '"F.Cu" "F.Mask" "F.Paste"', *net2),
        ]
        return _footprint(library, reference, value, x, 105 if capacitor else 102, pads)

    connector_pads = [
        _pad("1", "thru_hole", "rect", 0, 0, "1.7 1.7", '"*.Cu" "*.Mask"', 2, "3V3", "1"),
        _pad("2", "thru_hole", "circle", 0, 2.54, "1.7 1.7", '"*.Cu" "*.Mask"', 1, "GND", "1"),
        _pad("3", "thru_hole", "circle", 0, 5.08, "1.7 1.7", '"*.Cu" "*.Mask"', 3, "SDA", "1"),
        _pad("4", "thru_hole", "circle", 0, 7.62, "1.7 1.7", '"*.Cu" "*.Mask"', 4, "SCL", "1"),
        _pad("5", "thru_hole", "circle", 0, 10.16, "1.7 1.7", '"*.Cu" "*.Mask"', 5, "ALERT", "1"),
    ]
    footprints = [
        _footprint("Package_SO:MSOP-8_3x3mm_P0.65mm", "U1", "MCP9808T-E/MS", 107, 107.5, u1_pads),
        two_pad("R1", "4.7k", 104, (2, "3V3"), (3, "SDA")),
        two_pad("R2", "4.7k", 107.2, (2, "3V3"), (4, "SCL")),
        two_pad("R3", "10k", 110.4, (2, "3V3"), (5, "ALERT")),
        two_pad("C1", "100nF", 102, (2, "3V3"), (1, "GND"), capacitor=True),
        _footprint("Connector_PinHeader_2.54mm:PinHeader_1x05_P2.54mm_Vertical", "J1", "Conn_01x05", 116, 102, connector_pads),
    ]
    routes = """
  (segment (start 101.225 101.2) (end 116 101.2) (width 0.25) (layer "B.Cu") (net 2))
  (segment (start 116 101.2) (end 116 102) (width 0.25) (layer "B.Cu") (net 2))
  (segment (start 101.225 105) (end 101.225 104) (width 0.25) (layer "F.Cu") (net 2))
  (segment (start 101.225 104) (end 101.225 101.2) (width 0.25) (layer "B.Cu") (net 2))
  (segment (start 103.175 102) (end 103.175 101.2) (width 0.25) (layer "F.Cu") (net 2))
  (segment (start 106.375 102) (end 106.375 101.2) (width 0.25) (layer "F.Cu") (net 2))
  (segment (start 109.575 102) (end 109.575 101.2) (width 0.25) (layer "F.Cu") (net 2))
  (segment (start 109.1125 106.525) (end 111 106.525) (width 0.25) (layer "F.Cu") (net 2))
  (segment (start 111 106.525) (end 111 101.2) (width 0.25) (layer "B.Cu") (net 2))

  (segment (start 104.825 102) (end 104.825 103.5) (width 0.25) (layer "F.Cu") (net 3))
  (segment (start 104.825 103.5) (end 103.8 104) (width 0.25) (layer "F.Cu") (net 3))
  (segment (start 103.8 104) (end 103.8 106.525) (width 0.25) (layer "F.Cu") (net 3))
  (segment (start 103.8 106.525) (end 104.8875 106.525) (width 0.25) (layer "F.Cu") (net 3))
  (segment (start 103.8 104) (end 113 104) (width 0.25) (layer "F.Cu") (net 3))
  (segment (start 113 104) (end 115 107.08) (width 0.25) (layer "F.Cu") (net 3))
  (segment (start 115 107.08) (end 116 107.08) (width 0.25) (layer "F.Cu") (net 3))

  (segment (start 108.025 102) (end 108.025 103.2) (width 0.25) (layer "F.Cu") (net 4))
  (segment (start 108.025 103.2) (end 102.5 103.2) (width 0.25) (layer "B.Cu") (net 4))
  (segment (start 102.5 103.2) (end 102.5 110.5) (width 0.25) (layer "B.Cu") (net 4))
  (segment (start 102.5 110.5) (end 114 110.5) (width 0.25) (layer "B.Cu") (net 4))
  (segment (start 114 110.5) (end 116 109.62) (width 0.25) (layer "B.Cu") (net 4))
  (segment (start 102.5 107.175) (end 103.8 107.175) (width 0.25) (layer "B.Cu") (net 4))
  (segment (start 103.8 107.175) (end 104.8875 107.175) (width 0.25) (layer "F.Cu") (net 4))

  (segment (start 111.225 102) (end 112 102) (width 0.25) (layer "F.Cu") (net 5))
  (segment (start 112 102) (end 112 109) (width 0.25) (layer "B.Cu") (net 5))
  (segment (start 112 109) (end 112 111.5) (width 0.25) (layer "F.Cu") (net 5))
  (segment (start 112 111.5) (end 103.8 111.5) (width 0.25) (layer "F.Cu") (net 5))
  (segment (start 103.8 111.5) (end 103.8 107.825) (width 0.25) (layer "F.Cu") (net 5))
  (segment (start 103.8 107.825) (end 104.8875 107.825) (width 0.25) (layer "F.Cu") (net 5))
  (segment (start 112 111.5) (end 116 112.16) (width 0.25) (layer "F.Cu") (net 5))

  (via (at 101.225 104) (size 0.8) (drill 0.4) (layers "F.Cu" "B.Cu") (net 2))
  (via (at 103.175 101.2) (size 0.8) (drill 0.4) (layers "F.Cu" "B.Cu") (net 2))
  (via (at 106.375 101.2) (size 0.8) (drill 0.4) (layers "F.Cu" "B.Cu") (net 2))
  (via (at 109.575 101.2) (size 0.8) (drill 0.4) (layers "F.Cu" "B.Cu") (net 2))
  (via (at 111 106.525) (size 0.8) (drill 0.4) (layers "F.Cu" "B.Cu") (net 2))
  (via (at 108.025 103.2) (size 0.8) (drill 0.4) (layers "F.Cu" "B.Cu") (net 4))
  (via (at 103.8 107.175) (size 0.8) (drill 0.4) (layers "F.Cu" "B.Cu") (net 4))
  (via (at 112 102) (size 0.8) (drill 0.4) (layers "F.Cu" "B.Cu") (net 5))
  (via (at 112 109) (size 0.8) (drill 0.4) (layers "F.Cu" "B.Cu") (net 5))
"""
    board = f'''(kicad_pcb
  (version 20240108)
  (generator "pcbnew")
  (generator_version "10.0")
  (general (thickness 1.6))
  (paper "A4")
  (layers
    (0 "F.Cu" signal)
    (31 "B.Cu" signal)
    (36 "B.SilkS" user "B.Silkscreen")
    (37 "F.SilkS" user "F.Silkscreen")
    (38 "B.Mask" user)
    (39 "F.Mask" user)
    (44 "Edge.Cuts" user)
    (46 "B.CrtYd" user "B.Courtyard")
    (47 "F.CrtYd" user "F.Courtyard")
    (48 "B.Fab" user)
    (49 "F.Fab" user)
  )
  (setup (pad_to_mask_clearance 0) (allow_soldermask_bridges_in_footprints no))
  (net 0 "")
  (net 1 "GND")
  (net 2 "3V3")
  (net 3 "SDA")
  (net 4 "SCL")
  (net 5 "ALERT")
{chr(10).join(footprints)}
  (gr_rect (start 100 100) (end 118 115) (stroke (width 0.05) (type default)) (fill none) (layer "Edge.Cuts"))
{routes}
  (zone
    (net 1)
    (net_name "GND")
    (layer "B.Cu")
    (uuid "12345678-1234-4234-8234-123456789abc")
    (hatch edge 0.5)
    (connect_pads (clearance 0.3))
    (min_thickness 0.25)
    (filled_areas_thickness no)
    (fill yes (thermal_gap 0.3) (thermal_bridge_width 0.3))
    (polygon (pts (xy 100.6 100.6) (xy 117.4 100.6) (xy 117.4 114.4) (xy 100.6 114.4)))
  )
  (embedded_fonts no)
)
'''
    destination = SOLUTIONS / "deepee-pcb-002/artifacts/mcp9808-breakout.kicad_pcb"
    _write(destination, board)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-schematic", action="store_true")
    args = parser.parse_args()
    if SOLUTIONS.exists():
        hardware_tasks = ["deepee-sch-001", "deepee-pcb-001", "deepee-pcb-002"]
        if not args.skip_schematic:
            hardware_tasks.append("deepee-sch-002")
        for task_id in hardware_tasks:
            shutil.rmtree(SOLUTIONS / task_id, ignore_errors=True)
    generate_repaired_schematic()
    generate_completed_adapter()
    if not args.skip_schematic:
        generate_breakout_schematic()
    generate_breakout_board()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
