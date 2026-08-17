# MAX3485 RS-485 interface: schematic

    A 3.3 V controller needs a half-duplex RS-485 port with termination, fail-safe biasing, direction control, local decoupling, and separate MCU and field connectors.

    Create the schematic from the empty starter and implement the complete electrical interface. Use the exact references, values, footprints, and nets below:

    - `U1` = `MAX3485`: pin 1 → `RO`, pin 2 → `RE_N`, pin 3 → `DE`, pin 4 → `DI`, pin 5 → `GND`, pin 6 → `A`, pin 7 → `B`, pin 8 → `3V3`
- `R1` = `120R`: pin 1 → `A`, pin 2 → `B`
- `R2` = `680R`: pin 1 → `3V3`, pin 2 → `A`
- `R3` = `680R`: pin 1 → `B`, pin 2 → `GND`
- `C1` = `100nF`: pin 1 → `3V3`, pin 2 → `GND`
- `J1` = `Conn_01x06`: pin 1 → `3V3`, pin 2 → `GND`, pin 3 → `RO`, pin 4 → `RE_N`, pin 5 → `DE`, pin 6 → `DI`
- `J2` = `Conn_01x03`: pin 1 → `A`, pin 2 → `B`, pin 3 → `GND`

    Use explicit labels for every named net. The finished schematic must export a
    netlist matching this connection table and pass KiCad ERC with no errors or
    warnings. Save it as `artifacts/max3485-rs485.kicad_sch`.
