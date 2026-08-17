# MAX3485 RS-485 interface: PCB

    A 3.3 V controller needs a half-duplex RS-485 port with termination, fail-safe biasing, direction control, local decoupling, and separate MCU and field connectors.

    Create a two-layer PCB from the empty starter using the connection table below. Keep a 60 mm × 40 mm rectangular outline and use the exact references,
    values, footprints, and pin nets below:

    - `U1` = `MAX3485`: pin 1 → `RO`, pin 2 → `RE_N`, pin 3 → `DE`, pin 4 → `DI`, pin 5 → `GND`, pin 6 → `A`, pin 7 → `B`, pin 8 → `3V3`
- `R1` = `120R`: pin 1 → `A`, pin 2 → `B`
- `R2` = `680R`: pin 1 → `3V3`, pin 2 → `A`
- `R3` = `680R`: pin 1 → `B`, pin 2 → `GND`
- `C1` = `100nF`: pin 1 → `3V3`, pin 2 → `GND`
- `J1` = `Conn_01x06`: pin 1 → `3V3`, pin 2 → `GND`, pin 3 → `RO`, pin 4 → `RE_N`, pin 5 → `DE`, pin 6 → `DI`
- `J2` = `Conn_01x03`: pin 1 → `A`, pin 2 → `B`, pin 3 → `GND`

    Route every named net and resolve all clearance, unconnected-item, and board-
    outline findings. Save the finished board as
    `artifacts/max3485-rs485.kicad_pcb`; it must pass KiCad DRC with no errors
    or warnings.

Use routed copper at least 0.25 mm wide on every named net.
