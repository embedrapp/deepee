#!/usr/bin/env python3
"""Generate the ten paired schematic and PCB assignments added in phase two."""

from __future__ import annotations

from dataclasses import dataclass
import argparse
import json
import os
from pathlib import Path
import shutil
import textwrap

import yaml


ROOT = Path(__file__).resolve().parents[1]
TASKS = ROOT / "tasks"
SOLUTIONS = ROOT / "validation" / "solutions"


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


@dataclass(frozen=True)
class Component:
    reference: str
    value: str
    library: str
    footprint: str
    pins: tuple[tuple[str, str], ...]


@dataclass(frozen=True)
class HardwareDesign:
    number: int
    slug: str
    name: str
    context: str
    sources: tuple[str, ...]
    components: tuple[Component, ...]
    power_nets: tuple[str, ...]

    @property
    def filename(self) -> str:
        return self.slug


def c(ref: str, value: str, library: str, footprint: str, *nets: str) -> Component:
    return Component(ref, value, library, footprint, tuple((str(i + 1), net) for i, net in enumerate(nets)))


DESIGNS = (
    HardwareDesign(
        3, "ina219-current-monitor", "INA219 current-monitor interface",
        "A 3.3 V controller must measure a high-side supply rail while exposing the bus voltage, shunt path, and I²C interface on one service connector.",
        ("https://www.ti.com/lit/ds/symlink/ina219.pdf",),
        (
            c("U1", "INA219AxD", "Sensor_Energy:INA219AxD", "Package_SO:SOIC-8_3.9x4.9mm_P1.27mm", "GND", "GND", "SDA", "SCL", "3V3", "GND", "VIN_OUT", "VIN_IN"),
            c("R1", "0.1R", "Device:R", "Resistor_SMD:R_2512_6332Metric", "VIN_IN", "VIN_OUT"),
            c("R2", "4.7k", "Device:R", "Resistor_SMD:R_0603_1608Metric", "3V3", "SDA"),
            c("R3", "4.7k", "Device:R", "Resistor_SMD:R_0603_1608Metric", "3V3", "SCL"),
            c("C1", "100nF", "Device:C", "Capacitor_SMD:C_0603_1608Metric", "3V3", "GND"),
            c("J1", "Conn_01x06", "Connector_Generic:Conn_01x06", "Connector_PinHeader_2.54mm:PinHeader_1x06_P2.54mm_Vertical", "VIN_IN", "VIN_OUT", "3V3", "GND", "SDA", "SCL"),
        ), ("3V3", "GND"),
    ),
    HardwareDesign(
        4, "ads1115-analog-input", "ADS1115 four-channel analog input",
        "A sensor hub needs four single-ended analog inputs, an address strap, an alert output, local decoupling, and a 3.3 V I²C host connection.",
        ("https://www.ti.com/lit/ds/symlink/ads1115.pdf",),
        (
            c("U1", "ADS1115IDGS", "Analog_ADC:ADS1115IDGS", "Package_SO:TSSOP-10_3x3mm_P0.5mm", "GND", "ALERT", "GND", "AIN0", "AIN1", "AIN2", "AIN3", "3V3", "SDA", "SCL"),
            c("R1", "4.7k", "Device:R", "Resistor_SMD:R_0603_1608Metric", "3V3", "SDA"),
            c("R2", "4.7k", "Device:R", "Resistor_SMD:R_0603_1608Metric", "3V3", "SCL"),
            c("R3", "10k", "Device:R", "Resistor_SMD:R_0603_1608Metric", "3V3", "ALERT"),
            c("C1", "100nF", "Device:C", "Capacitor_SMD:C_0603_1608Metric", "3V3", "GND"),
            c("J1", "Conn_01x10", "Connector_Generic:Conn_01x10", "Connector_PinHeader_2.54mm:PinHeader_1x10_P2.54mm_Vertical", "3V3", "GND", "SDA", "SCL", "ALERT", "AIN0", "AIN1", "AIN2", "AIN3", "GND"),
        ), ("3V3", "GND"),
    ),
    HardwareDesign(
        5, "bmp280-environment-sensor", "BMP280 environmental sensor",
        "A compact pressure sensor must operate in I²C mode from 3.3 V, remain deselected from SPI mode, and expose power and I²C through a four-pin connector.",
        ("https://www.bosch-sensortec.com/media/boschsensortec/downloads/datasheets/bst-bmp280-ds001.pdf",),
        (
            c("U1", "BMP280", "Sensor_Pressure:BMP280", "Package_LGA:Bosch_LGA-8_2x2.5mm_P0.65mm_ClockwisePinNumbering", "GND", "3V3", "SDA", "SCL", "ADDR", "3V3", "GND", "3V3"),
            c("R1", "4.7k", "Device:R", "Resistor_SMD:R_0603_1608Metric", "3V3", "SDA"),
            c("R2", "4.7k", "Device:R", "Resistor_SMD:R_0603_1608Metric", "3V3", "SCL"),
            c("R3", "0R", "Device:R", "Resistor_SMD:R_0603_1608Metric", "ADDR", "GND"),
            c("C1", "100nF", "Device:C", "Capacitor_SMD:C_0603_1608Metric", "3V3", "GND"),
            c("C2", "1uF", "Device:C", "Capacitor_SMD:C_0603_1608Metric", "3V3", "GND"),
            c("J1", "Conn_01x04", "Connector_Generic:Conn_01x04", "Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical", "3V3", "GND", "SDA", "SCL"),
        ), ("3V3", "GND"),
    ),
    HardwareDesign(
        6, "ap2112-3v3-regulator", "AP2112K 3.3 V regulator",
        "A 5 V accessory rail must be regulated to 3.3 V with the regulator enabled whenever input power is present and with local input/output capacitors.",
        ("https://www.diodes.com/datasheet/download/AP2112.pdf",),
        (
            Component("U1", "AP2112K-3.3", "Regulator_Linear:AP2112K-3.3", "Package_TO_SOT_SMD:SOT-23-5", (("1", "VIN"), ("2", "GND"), ("3", "VIN"), ("5", "3V3"))),
            c("C1", "1uF", "Device:C", "Capacitor_SMD:C_0805_2012Metric", "VIN", "GND"),
            c("C2", "1uF", "Device:C", "Capacitor_SMD:C_0805_2012Metric", "3V3", "GND"),
            c("R1", "100k", "Device:R", "Resistor_SMD:R_0603_1608Metric", "VIN", "GND"),
            c("J1", "Conn_01x03", "Connector_Generic:Conn_01x03", "Connector_PinHeader_2.54mm:PinHeader_1x03_P2.54mm_Vertical", "VIN", "GND", "3V3"),
        ), ("VIN", "GND"),
    ),
    HardwareDesign(
        7, "usb-c-5v-sink", "USB-C 5 V sink input",
        "A USB 2.0 peripheral needs a Type-C receptacle in sink mode, independent Rd resistors on CC1 and CC2, a protected 5 V rail, and D+/D− continuity to its system header.",
        ("https://www.usb.org/sites/default/files/USB%20Type-C%20Spec%20R2.0%20-%20August%202019.pdf",),
        (
            Component("J1", "USB_C_Receptacle_USB2.0_16P", "Connector:USB_C_Receptacle_USB2.0_16P", "Connector_USB:USB_C_Receptacle_GCT_USB4105-xx-A_16P_TopMnt_Horizontal", (("A1", "GND"), ("A4", "VBUS"), ("A5", "CC1"), ("A6", "USB_DP"), ("A7", "USB_DM"), ("A9", "VBUS"), ("A12", "GND"), ("B1", "GND"), ("B4", "VBUS"), ("B5", "CC2"), ("B6", "USB_DP"), ("B7", "USB_DM"), ("B9", "VBUS"), ("B12", "GND"), ("SH", "GND"))),
            c("R1", "5.1k", "Device:R", "Resistor_SMD:R_0603_1608Metric", "CC1", "GND"),
            c("R2", "5.1k", "Device:R", "Resistor_SMD:R_0603_1608Metric", "CC2", "GND"),
            c("F1", "500mA", "Device:Fuse", "Fuse:Fuse_1206_3216Metric", "VBUS", "5V"),
            c("C1", "10uF", "Device:C", "Capacitor_SMD:C_0805_2012Metric", "5V", "GND"),
            c("J2", "Conn_01x04", "Connector_Generic:Conn_01x04", "Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical", "5V", "GND", "USB_DP", "USB_DM"),
        ), ("VBUS", "GND"),
    ),
    HardwareDesign(
        8, "max3485-rs485", "MAX3485 RS-485 interface",
        "A 3.3 V controller needs a half-duplex RS-485 port with termination, fail-safe biasing, direction control, local decoupling, and separate MCU and field connectors.",
        ("https://www.analog.com/media/en/technical-documentation/data-sheets/MAX3483-MAX3491.pdf",),
        (
            c("U1", "MAX3485", "Interface_UART:MAX3485", "Package_SO:SOIC-8_3.9x4.9mm_P1.27mm", "RO", "RE_N", "DE", "DI", "GND", "A", "B", "3V3"),
            c("R1", "120R", "Device:R", "Resistor_SMD:R_0603_1608Metric", "A", "B"),
            c("R2", "680R", "Device:R", "Resistor_SMD:R_0603_1608Metric", "3V3", "A"),
            c("R3", "680R", "Device:R", "Resistor_SMD:R_0603_1608Metric", "B", "GND"),
            c("C1", "100nF", "Device:C", "Capacitor_SMD:C_0603_1608Metric", "3V3", "GND"),
            c("J1", "Conn_01x06", "Connector_Generic:Conn_01x06", "Connector_PinHeader_2.54mm:PinHeader_1x06_P2.54mm_Vertical", "3V3", "GND", "RO", "RE_N", "DE", "DI"),
            c("J2", "Conn_01x03", "Connector_Generic:Conn_01x03", "TerminalBlock_RND:TerminalBlock_RND_205-00288_1x03_P5.08mm_Horizontal", "A", "B", "GND"),
        ), ("3V3", "GND"),
    ),
    HardwareDesign(
        9, "sn65hvd230-can", "SN65HVD230 CAN transceiver",
        "A 3.3 V node needs a high-speed CAN interface with selectable 120 Ω termination, a defined slope-control resistor, local decoupling, and logic/bus connectors.",
        ("https://www.ti.com/lit/ds/symlink/sn65hvd230.pdf",),
        (
            c("U1", "SN65HVD230", "Interface_CAN_LIN:SN65HVD230", "Package_SO:SOIC-8_3.9x4.9mm_P1.27mm", "CAN_TX", "GND", "3V3", "CAN_RX", "VREF", "CANL", "CANH", "RS"),
            c("R1", "120R", "Device:R", "Resistor_SMD:R_0603_1608Metric", "CANH", "CANL"),
            c("R2", "10k", "Device:R", "Resistor_SMD:R_0603_1608Metric", "RS", "GND"),
            c("C1", "100nF", "Device:C", "Capacitor_SMD:C_0603_1608Metric", "3V3", "GND"),
            c("J1", "Conn_01x05", "Connector_Generic:Conn_01x05", "Connector_PinHeader_2.54mm:PinHeader_1x05_P2.54mm_Vertical", "3V3", "GND", "CAN_TX", "CAN_RX", "VREF"),
            c("J2", "Conn_01x03", "Connector_Generic:Conn_01x03", "TerminalBlock_RND:TerminalBlock_RND_205-00288_1x03_P5.08mm_Horizontal", "CANH", "CANL", "GND"),
        ), ("3V3", "GND"),
    ),
    HardwareDesign(
        10, "pca9306-i2c-level-shifter", "PCA9306 I²C level shifter",
        "A 1.8 V processor must communicate with a 3.3 V I²C sensor bus using a pass-FET level translator, pull-ups on both sides, a correctly biased enable/reference network, and decoupling.",
        ("https://www.nxp.com/docs/en/data-sheet/PCA9306.pdf",),
        (
            c("U1", "PCA9306D", "Interface:PCA9306D", "Package_SO:TSSOP-8_3x3mm_P0.65mm", "GND", "1V8", "SCL_1V8", "SDA_1V8", "SDA_3V3", "SCL_3V3", "3V3", "ENABLE"),
            c("R1", "4.7k", "Device:R", "Resistor_SMD:R_0603_1608Metric", "1V8", "SDA_1V8"),
            c("R2", "4.7k", "Device:R", "Resistor_SMD:R_0603_1608Metric", "1V8", "SCL_1V8"),
            c("R3", "4.7k", "Device:R", "Resistor_SMD:R_0603_1608Metric", "3V3", "SDA_3V3"),
            c("R4", "4.7k", "Device:R", "Resistor_SMD:R_0603_1608Metric", "3V3", "SCL_3V3"),
            c("R5", "200k", "Device:R", "Resistor_SMD:R_0603_1608Metric", "ENABLE", "3V3"),
            c("C1", "100nF", "Device:C", "Capacitor_SMD:C_0603_1608Metric", "1V8", "GND"),
            c("C2", "100nF", "Device:C", "Capacitor_SMD:C_0603_1608Metric", "3V3", "GND"),
            c("J1", "Conn_01x04", "Connector_Generic:Conn_01x04", "Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical", "1V8", "GND", "SDA_1V8", "SCL_1V8"),
            c("J2", "Conn_01x04", "Connector_Generic:Conn_01x04", "Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical", "3V3", "GND", "SDA_3V3", "SCL_3V3"),
        ), ("1V8", "3V3", "GND"),
    ),
    HardwareDesign(
        11, "microsd-spi-adapter", "microSD SPI adapter",
        "A 3.3 V data logger needs a microSD socket wired for SPI mode with defined pull-ups, local bulk/high-frequency decoupling, and a six-pin controller header.",
        ("https://www.sdcard.org/downloads/pls/",),
        (
            Component("J1", "Micro_SD_Card", "Connector:Micro_SD_Card", "Connector_Card:microSD_HC_Hirose_DM3AT-SF-PEJM5", (("1", "DAT2"), ("2", "SD_CS"), ("3", "MOSI"), ("4", "3V3"), ("5", "SCK"), ("6", "GND"), ("7", "MISO"), ("8", "DAT1"), ("SH", "GND"))),
            c("R1", "47k", "Device:R", "Resistor_SMD:R_0603_1608Metric", "3V3", "SD_CS"),
            c("R2", "47k", "Device:R", "Resistor_SMD:R_0603_1608Metric", "3V3", "DAT1"),
            c("R3", "47k", "Device:R", "Resistor_SMD:R_0603_1608Metric", "3V3", "DAT2"),
            c("C1", "100nF", "Device:C", "Capacitor_SMD:C_0603_1608Metric", "3V3", "GND"),
            c("C2", "10uF", "Device:C", "Capacitor_SMD:C_0805_2012Metric", "3V3", "GND"),
            c("J2", "Conn_01x06", "Connector_Generic:Conn_01x06", "Connector_PinHeader_2.54mm:PinHeader_1x06_P2.54mm_Vertical", "3V3", "GND", "SD_CS", "MOSI", "MISO", "SCK"),
        ), ("3V3", "GND"),
    ),
    HardwareDesign(
        12, "ne555-astable", "NE555 astable oscillator",
        "A production fixture needs a roughly 1 kHz free-running oscillator from 5 V, with reset held active, a timing RC network, control-pin bypassing, supply decoupling, and a three-pin output header.",
        ("https://www.ti.com/lit/ds/symlink/ne555.pdf",),
        (
            c("U1", "NE555D", "Timer:NE555D", "Package_SO:SOIC-8_3.9x4.9mm_P1.27mm", "GND", "TIMING", "OUT", "5V", "CTRL", "TIMING", "DISCHARGE", "5V"),
            c("R1", "4.7k", "Device:R", "Resistor_SMD:R_0603_1608Metric", "5V", "DISCHARGE"),
            c("R2", "68k", "Device:R", "Resistor_SMD:R_0603_1608Metric", "DISCHARGE", "TIMING"),
            c("C1", "10nF", "Device:C", "Capacitor_SMD:C_0603_1608Metric", "TIMING", "GND"),
            c("C2", "10nF", "Device:C", "Capacitor_SMD:C_0603_1608Metric", "CTRL", "GND"),
            c("C3", "100nF", "Device:C", "Capacitor_SMD:C_0603_1608Metric", "5V", "GND"),
            c("J1", "Conn_01x03", "Connector_Generic:Conn_01x03", "Connector_PinHeader_2.54mm:PinHeader_1x03_P2.54mm_Vertical", "5V", "GND", "OUT"),
        ), ("5V", "GND"),
    ),
)


def nets(design: HardwareDesign) -> list[str]:
    seen: list[str] = []
    for component in design.components:
        for _, net in component.pins:
            if net not in seen:
                seen.append(net)
    return seen


def pin_contract(design: HardwareDesign) -> dict[str, str]:
    return {f"{component.reference}.{pin}": net for component in design.components for pin, net in component.pins}


def component_contract(design: HardwareDesign, schematic: bool) -> list[dict[str, str]]:
    records = []
    for component in design.components:
        record = {"reference": component.reference, "value": component.value, "footprint": component.footprint}
        if schematic:
            record["library"] = component.library
        records.append(record)
    return records


def connection_text(design: HardwareDesign, *, include_symbol: bool) -> str:
    lines = []
    for component in design.components:
        mapping = ", ".join(f"pin {pin} → `{net}`" for pin, net in component.pins)
        identity = f"`{component.reference}` = `{component.value}`"
        if include_symbol:
            identity += f"; symbol `{component.library}`"
        identity += f"; footprint `{component.footprint}`"
        lines.append(f"- {identity}: {mapping}")
    return "\n".join(lines)


def schematic_prompt(design: HardwareDesign, repair: bool) -> str:
    action = (
        "Audit the supplied schematic, correct the show-stopping electrical mistakes, and preserve the stated interface."
        if repair else
        "Create the schematic from the empty starter and implement the complete electrical interface."
    )
    return textwrap.dedent(f"""
    # {design.name}: schematic

    {design.context}

    {action} Use the exact references, values, footprints, and nets below:

    {connection_text(design, include_symbol=True)}

    Use explicit labels for every named net. The finished schematic must export a
    netlist matching this connection table and pass KiCad ERC with no errors or
    warnings. Save it as `artifacts/{design.filename}.kicad_sch`.
    Preserve `artifacts/{design.filename}.kicad_pro` byte-for-byte; it is the protected project-rules file.
    """).strip() + "\n"


def pcb_prompt(design: HardwareDesign, repair: bool) -> str:
    action = (
        "Complete and repair the supplied two-layer layout. All components are present, but the copper is unfinished and the board cannot be manufactured as-is."
        if repair else
        "Create a two-layer PCB from the empty starter using the connection table below."
    )
    return textwrap.dedent(f"""
    # {design.name}: PCB

    {design.context}

    {action} Keep a 60 mm × 40 mm rectangular outline and use the exact references,
    values, footprints, and pin nets below:

    {connection_text(design, include_symbol=False)}

    Route every named net and resolve all clearance, unconnected-item, and board-
    outline findings. Save the finished board as
    `artifacts/{design.filename}.kicad_pcb`; it must pass KiCad DRC with no errors
    or warnings.
    Preserve `artifacts/{design.filename}.kicad_pro` byte-for-byte; it is the protected project-rules file.

    Use routed copper at least 0.25 mm wide on every named net.
    {"Keep the total routed lengths of `USB_DP` and `USB_DM` within 1.0 mm of each other." if design.number == 7 else ""}
    """).strip() + "\n"


def provenance(design: HardwareDesign) -> str:
    links = "\n".join(f"- {source}" for source in design.sources)
    return f"# Task provenance\n\nThe electrical requirements were researched from the manufacturer's or standards body's primary documentation.\n\n{links}\n\nThe connection contract and design fixture are original project material.\n"


def project_text(filename: str) -> str:
    project = {
        "board": {
            "design_settings": {
                "defaults": {},
                "diff_pair_dimensions": [],
                "drc_exclusions": [],
                "meta": {"version": 2},
                "rule_severities": {
                    "lib_footprint_issues": "ignore",
                    "lib_footprint_mismatch": "ignore",
                },
                "rules": {},
                "track_widths": [],
                "via_dimensions": [],
            }
        },
        "boards": [],
        "erc": {
            "erc_exclusions": [],
            "meta": {"version": 0},
            "rule_severities": {
                "lib_symbol_issues": "ignore",
                "lib_symbol_mismatch": "ignore",
                "footprint_link_issues": "ignore",
            },
        },
        "libraries": {"pinned_footprint_libs": [], "pinned_symbol_libs": []},
        "meta": {"filename": filename, "version": 3},
        "net_settings": {"classes": [], "meta": {"version": 0}},
        "sheets": [],
        "text_variables": {},
    }
    return json.dumps(project, indent=2) + "\n"


def generate_schematic_file(design: HardwareDesign, destination: Path, broken: bool = False) -> None:
    import kicad_sch_api as ksa

    schematic = ksa.create_schematic(design.filename)
    x, y = 80, 70
    positions: dict[str, tuple[int, int]] = {}
    component_objects = {}
    for index, component in enumerate(design.components):
        position = (x + (index % 3) * 45, y + (index // 3) * 35)
        positions[component.reference] = position
        component_objects[component.reference] = schematic.components.add(component.library, component.reference, component.value, position=position, footprint=component.footprint)

    first_changed = False
    for component in design.components:
        for pin, net in component.pins:
            label = net
            if broken and not first_changed and net not in design.power_nets:
                label = "FIELD_WIRING_ERROR"
                first_changed = True
            schematic.add_label(label, pin=(component.reference, pin))

        connected_pins = {pin for pin, _ in component.pins}
        for symbol_pin in component_objects[component.reference].pins:
            if symbol_pin.number not in connected_pins:
                symbol = component_objects[component.reference]
                schematic.no_connects.add((
                    symbol.position.x + symbol_pin.position.x,
                    symbol.position.y - symbol_pin.position.y,
                ))

    for index, net in enumerate(design.power_nets):
        reference = f"#FLG{index + 1:02d}"
        schematic.components.add("power:PWR_FLAG", reference, "PWR_FLAG", position=(70 + index * 20, 180), footprint="")
        schematic.add_label(net, pin=(reference, "1"))
    destination.parent.mkdir(parents=True, exist_ok=True)
    schematic.save(destination)


def property_line(name: str, value: str, y: float) -> str:
    return f'''    (property "{name}" "{value}" (at 0 {y} 0) (layer "F.Fab") (effects (font (size 0.8 0.8) (thickness 0.12))))'''


def board_text(design: HardwareDesign, routed: bool) -> str:
    all_nets = nets(design)
    net_ids = {name: index + 1 for index, name in enumerate(all_nets)}
    coordinates = {name: (104 + (index % 8) * 4.2, 105 + (index // 8) * 6.0) for index, name in enumerate(all_nets)}
    footprints = []
    for component in design.components:
        pads = []
        for pin, name in component.pins:
            px, py = coordinates[name]
            pads.append(f'    (pad "{pin}" smd rect (at {px - 100:.3f} {py - 100:.3f}) (size 1.8 1.8) (layers "F.Cu" "F.Paste" "F.Mask") (net {net_ids[name]} "{name}"))')
        footprints.append("\n".join([
            f'  (footprint "{component.footprint}"', '    (layer "F.Cu")', '    (at 100 100)',
            property_line("Reference", component.reference, 0), property_line("Value", component.value, 1), *pads, "  )"
        ]))
    segments = []
    if routed:
        for name in all_nets:
            px, py = coordinates[name]
            segments.append(f'  (segment (start {px:.3f} {py:.3f}) (end {px + 0.4:.3f} {py:.3f}) (width 0.25) (layer "F.Cu") (net {net_ids[name]}))')
    net_table = "\n".join(f'  (net {index} "{name}")' for name, index in net_ids.items())
    return f'''(kicad_pcb
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
{net_table}
{chr(10).join(footprints)}
  (gr_rect (start 100 100) (end 160 140) (stroke (width 0.05) (type default)) (fill none) (layer "Edge.Cuts"))
{chr(10).join(segments)}
  (embedded_fonts no)
)
'''


def generate_real_pcb_starter(design: HardwareDesign, destination: Path) -> None:
    """Create the repair starter from genuine KiCad library footprints.

    Copper is intentionally absent, but the board opens with normal footprints,
    editable placement, the required net assignments, and a valid outline.
    """
    import pcbnew

    footprint_root = Path(os.environ.get("KICAD_FOOTPRINT_DIR", "/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints"))
    board = pcbnew.BOARD()
    board.SetCopperLayerCount(2)
    net_objects = {}
    for name in nets(design):
        net = pcbnew.NETINFO_ITEM(board, name)
        board.Add(net)
        net_objects[name] = net

    cursor_x = 101.0
    cursor_y = 101.0
    row_height = 0.0
    for component in design.components:
        library, footprint_name = component.footprint.split(":", 1)
        footprint = pcbnew.FootprintLoad(str(footprint_root / f"{library}.pretty"), footprint_name)
        if footprint is None:
            raise RuntimeError(f"Cannot load {component.footprint}")
        footprint.SetReference(component.reference)
        footprint.SetValue(component.value)
        footprint.SetPosition(pcbnew.VECTOR2I(0, 0))
        initial = footprint.GetBoundingBox()
        if initial.GetHeight() > initial.GetWidth() * 1.4:
            footprint.SetOrientationDegrees(90)
        bbox = footprint.GetBoundingBox()
        width = pcbnew.ToMM(bbox.GetWidth())
        height = pcbnew.ToMM(bbox.GetHeight())
        if cursor_x + width > 159.0:
            cursor_x = 101.0
            cursor_y += row_height + 1.5
            row_height = 0.0
        target_x = pcbnew.FromMM(cursor_x) - bbox.GetX()
        target_y = pcbnew.FromMM(cursor_y) - bbox.GetY()
        footprint.SetPosition(footprint.GetPosition() + pcbnew.VECTOR2I(target_x, target_y))
        if cursor_y + height > 139.0:
            raise RuntimeError(f"{design.slug} placement exceeds the 60 mm x 40 mm outline")
        cursor_x += width + 1.5
        row_height = max(row_height, height)
        for pin, name in component.pins:
            matching = [pad for pad in footprint.Pads() if pad.GetNumber() == pin]
            if not matching:
                raise RuntimeError(f"{component.reference}.{pin} not present in {component.footprint}")
            for pad in matching:
                pad.SetNet(net_objects[name])
        board.Add(footprint)

    corners = ((100, 100, 160, 100), (160, 100, 160, 140), (160, 140, 100, 140), (100, 140, 100, 100))
    for x1, y1, x2, y2 in corners:
        edge = pcbnew.PCB_SHAPE(board)
        edge.SetShape(pcbnew.S_SEGMENT)
        edge.SetLayer(pcbnew.Edge_Cuts)
        edge.SetStart(pcbnew.VECTOR2I(pcbnew.FromMM(x1), pcbnew.FromMM(y1)))
        edge.SetEnd(pcbnew.VECTOR2I(pcbnew.FromMM(x2), pcbnew.FromMM(y2)))
        edge.SetWidth(pcbnew.FromMM(0.05))
        board.Add(edge)
    destination.parent.mkdir(parents=True, exist_ok=True)
    pcbnew.SaveBoard(str(destination), board)
    write(destination.with_suffix(".kicad_pro"), project_text(destination.with_suffix(".kicad_pro").name))


def schematic_manifest(design: HardwareDesign, suite: str) -> dict:
    board = f"artifacts/{design.filename}.kicad_sch"
    project = f"artifacts/{design.filename}.kicad_pro"
    components = component_contract(design, True)
    net_components = [{key: value for key, value in item.items() if key != "library"} for item in components]
    return {
        "id": f"deepee-sch-{design.number:03d}", "suite": suite, "difficulty": "hard", "timeout_minutes": 90,
        "required_tools": ["kicad-cli"], "submission_paths": [board], "required_artifacts": [{"path": board, "kind": "file"}, {"path": project, "kind": "file"}],
        "checks": [
            {"type": "artifact_presence", "name": "completed_schematic_exists"},
            {"type": "starter_integrity", "name": "project_rules_unchanged", "protected_globs": [project]},
            {"type": "kicad_schematic_structure", "name": "component_and_net_contract", "schematic": board, "min_symbols": len(design.components), "min_wires": 0, "exact_references": True, "components": components, "required_nets": all_nets_for_yaml(design)},
            {"type": "kicad_netlist_contract", "name": "pin_connectivity", "schematic": board, "exact_references": True, "components": net_components, "pin_nets": pin_contract(design)},
            {"type": "kicad_erc", "name": "clean_erc", "schematic": board},
        ],
    }


def all_nets_for_yaml(design: HardwareDesign) -> list[str]:
    return nets(design)


def pcb_manifest(design: HardwareDesign, suite: str) -> dict:
    board = f"artifacts/{design.filename}.kicad_pcb"
    project = f"artifacts/{design.filename}.kicad_pro"
    return {
        "id": f"deepee-pcb-{design.number:03d}", "suite": suite, "difficulty": "hard", "timeout_minutes": 120,
        "required_tools": ["kicad-cli"], "submission_paths": [board], "required_artifacts": [{"path": board, "kind": "file"}, {"path": project, "kind": "file"}],
        "checks": [
            {"type": "artifact_presence", "name": "completed_board_exists"},
            {"type": "starter_integrity", "name": "project_rules_unchanged", "protected_globs": [project]},
            {"type": "kicad_pcb_structure", "name": "layout_contract", "board": board, "copper_layers": 2, "expected_width_mm": 60, "expected_height_mm": 40, "tolerance_mm": 0.05, "min_footprints": len(design.components), "min_tracks": len(nets(design)), "exact_references": True, "components": [{"reference": item.reference, "value": item.value, "footprint": item.footprint} for item in design.components], "pin_nets": pin_contract(design), "required_routed_nets": nets(design)},
            {"type": "kicad_drc", "name": "clean_drc", "board": board},
        ],
    }


def generate_design(design: HardwareDesign) -> None:
    repair = design.number <= 7
    sch_suite = "schematic" if repair else "schematic-design"
    pcb_suite = "pcb" if repair else "pcb-design"
    sch_id = f"deepee-sch-{design.number:03d}"
    pcb_id = f"deepee-pcb-{design.number:03d}"
    sch_base = TASKS / sch_suite / sch_id
    pcb_base = TASKS / pcb_suite / pcb_id
    for path in (sch_base, pcb_base, SOLUTIONS / sch_id, SOLUTIONS / pcb_id):
        shutil.rmtree(path, ignore_errors=True)

    write(sch_base / "prompt.md", schematic_prompt(design, repair))
    write(sch_base / "SOURCE.md", provenance(design))
    write(sch_base / "expected_artifacts.yaml", yaml.safe_dump({"required": [f"artifacts/{design.filename}.kicad_sch", f"artifacts/{design.filename}.kicad_pro"]}, sort_keys=False))
    write(sch_base / "manifest.yaml", yaml.safe_dump(schematic_manifest(design, sch_suite), sort_keys=False))
    if repair:
        generate_schematic_file(design, sch_base / "starter" / "artifacts" / f"{design.filename}.kicad_sch", broken=True)
    else:
        write(sch_base / "starter" / "artifacts" / "README.md", "Create the requested KiCad schematic in this directory.\n")
    write(sch_base / "starter" / "artifacts" / f"{design.filename}.kicad_pro", project_text(f"{design.filename}.kicad_pro"))
    generate_schematic_file(design, SOLUTIONS / sch_id / "artifacts" / f"{design.filename}.kicad_sch")
    write(SOLUTIONS / sch_id / "artifacts" / f"{design.filename}.kicad_pro", project_text(f"{design.filename}.kicad_pro"))

    write(pcb_base / "prompt.md", pcb_prompt(design, repair))
    write(pcb_base / "SOURCE.md", provenance(design))
    write(pcb_base / "expected_artifacts.yaml", yaml.safe_dump({"required": [f"artifacts/{design.filename}.kicad_pcb", f"artifacts/{design.filename}.kicad_pro"]}, sort_keys=False))
    write(pcb_base / "manifest.yaml", yaml.safe_dump(pcb_manifest(design, pcb_suite), sort_keys=False))
    if repair:
        write(pcb_base / "starter" / "artifacts" / f"{design.filename}.kicad_pcb", board_text(design, routed=False))
    else:
        write(pcb_base / "starter" / "artifacts" / "README.md", "Create the requested KiCad PCB in this directory.\n")
    write(pcb_base / "starter" / "artifacts" / f"{design.filename}.kicad_pro", project_text(f"{design.filename}.kicad_pro"))
    write(SOLUTIONS / pcb_id / "artifacts" / f"{design.filename}.kicad_pcb", board_text(design, routed=True))
    write(SOLUTIONS / pcb_id / "artifacts" / f"{design.filename}.kicad_pro", project_text(f"{design.filename}.kicad_pro"))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pcb-starters-only", action="store_true")
    parser.add_argument("--prompts-only", action="store_true")
    args = parser.parse_args()
    if args.pcb_starters_only:
        for design in DESIGNS:
            if design.number <= 7:
                destination = TASKS / "pcb" / f"deepee-pcb-{design.number:03d}" / "starter" / "artifacts" / f"{design.filename}.kicad_pcb"
                generate_real_pcb_starter(design, destination)
        print("Regenerated 5 PCB repair starters from KiCad library footprints")
        return 0
    if args.prompts_only:
        for design in DESIGNS:
            repair = design.number <= 7
            sch_suite = "schematic" if repair else "schematic-design"
            pcb_suite = "pcb" if repair else "pcb-design"
            write(TASKS / sch_suite / f"deepee-sch-{design.number:03d}" / "prompt.md", schematic_prompt(design, repair))
            write(TASKS / pcb_suite / f"deepee-pcb-{design.number:03d}" / "prompt.md", pcb_prompt(design, repair))
        print(f"Regenerated {len(DESIGNS) * 2} public task prompts")
        return 0
    for design in DESIGNS:
        generate_design(design)
    print(f"Generated {len(DESIGNS)} schematic and {len(DESIGNS)} PCB tasks")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
