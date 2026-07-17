# Design an MCP9808 temperature-sensor breakout schematic

Create a KiCad 10 schematic from scratch for a 3.3 V MCP9808 breakout. Use exactly these non-power components and footprints:

- `U1`: Microchip `MCP9808T-E/MS`, symbol `Sensor_Temperature:MCP9808_MSOP`, footprint `Package_SO:MSOP-8_3x3mm_P0.65mm`;
- `R1`, `R2`: `4.7k`, `Device:R`, footprint `Resistor_SMD:R_0603_1608Metric`;
- `R3`: `10k`, `Device:R`, footprint `Resistor_SMD:R_0603_1608Metric`;
- `C1`: `100nF`, `Device:C`, footprint `Capacitor_SMD:C_0603_1608Metric`;
- `J1`: `Conn_01x05`, `Connector_Generic:Conn_01x05`, footprint `Connector_PinHeader_2.54mm:PinHeader_1x05_P2.54mm_Vertical`.

Electrical contract:

- `U1`: pin 1 `SDA`, pin 2 `SCL`, pin 3 `ALERT`, pin 4 `GND`, pins 5/6/7 (`A2/A1/A0`) `GND`, pin 8 `3V3`;
- `R1`: pin 1 `3V3`, pin 2 `SDA`; `R2`: pin 1 `3V3`, pin 2 `SCL`;
- `R3`: pin 1 `3V3`, pin 2 `ALERT`;
- `C1`: pin 1 `3V3`, pin 2 `GND`;
- `J1`: pin 1 `3V3`, pin 2 `GND`, pin 3 `SDA`, pin 4 `SCL`, pin 5 `ALERT`.

The address pins tied low select address `0x18`. `R3` is the required pull-up for the open-drain `ALERT` output. Add the power symbols/flags needed for clean ERC, but add no other non-power components.

Submit `artifacts/mcp9808-breakout.kicad_sch`. The exported netlist must satisfy the pin contract and ERC must report no errors or warnings. Drawing coordinates and wire shape are not compared with a golden schematic.
