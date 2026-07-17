# Design and route an MCP9808 breakout PCB

Create a manufacturable KiCad 10 PCB from scratch for the fixed MCP9808 breakout contract below. The board must have a rectangular 18 mm × 15 mm outline and use two copper layers.

Components:

- `U1`: `MCP9808T-E/MS`, footprint `Package_SO:MSOP-8_3x3mm_P0.65mm`;
- `R1`, `R2`: `4.7k`, footprint `Resistor_SMD:R_0603_1608Metric`;
- `R3`: `10k`, footprint `Resistor_SMD:R_0603_1608Metric`;
- `C1`: `100nF`, footprint `Capacitor_SMD:C_0603_1608Metric`;
- `J1`: `Conn_01x05`, footprint `Connector_PinHeader_2.54mm:PinHeader_1x05_P2.54mm_Vertical`.

Pad-to-net contract:

- `U1`: 1 `SDA`, 2 `SCL`, 3 `ALERT`, 4/5/6/7 `GND`, 8 `3V3`;
- `R1`: 1 `3V3`, 2 `SDA`; `R2`: 1 `3V3`, 2 `SCL`;
- `R3`: 1 `3V3`, 2 `ALERT`;
- `C1`: 1 `3V3`, 2 `GND`;
- `J1`: 1 `3V3`, 2 `GND`, 3 `SDA`, 4 `SCL`, 5 `ALERT`.

Place and route the board using any valid geometry. Include a GND copper zone. Do not add or remove components or alter the outline dimensions.

Submit `artifacts/mcp9808-breakout.kicad_pcb`. It must preserve the exact footprint/pad contract, connect every pad, and pass KiCad DRC with no errors or warnings. Placement and trace geometry are intentionally not compared with a golden board.
