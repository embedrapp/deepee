# MAX3485 RS-485 interface: PCB

    A 3.3 V controller needs a half-duplex RS-485 port with termination, fail-safe biasing, direction control, local decoupling, and separate MCU and field connectors.

    Create a two-layer PCB from the empty starter using the connection table below. Keep a 60 mm × 40 mm rectangular outline and use the exact references,
    values, footprints, and pin nets below:

    - `U1` = `MAX3485`; footprint `Package_SO:SOIC-8_3.9x4.9mm_P1.27mm`: pin 1 → `RO`, pin 2 → `RE_N`, pin 3 → `DE`, pin 4 → `DI`, pin 5 → `GND`, pin 6 → `A`, pin 7 → `B`, pin 8 → `3V3`
- `R1` = `120R`; footprint `Resistor_SMD:R_0603_1608Metric`: pin 1 → `A`, pin 2 → `B`
- `R2` = `680R`; footprint `Resistor_SMD:R_0603_1608Metric`: pin 1 → `3V3`, pin 2 → `A`
- `R3` = `680R`; footprint `Resistor_SMD:R_0603_1608Metric`: pin 1 → `B`, pin 2 → `GND`
- `C1` = `100nF`; footprint `Capacitor_SMD:C_0603_1608Metric`: pin 1 → `3V3`, pin 2 → `GND`
- `J1` = `Conn_01x06`; footprint `Connector_PinHeader_2.54mm:PinHeader_1x06_P2.54mm_Vertical`: pin 1 → `3V3`, pin 2 → `GND`, pin 3 → `RO`, pin 4 → `RE_N`, pin 5 → `DE`, pin 6 → `DI`
- `J2` = `Conn_01x03`; footprint `TerminalBlock_RND:TerminalBlock_RND_205-00288_1x03_P5.08mm_Horizontal`: pin 1 → `A`, pin 2 → `B`, pin 3 → `GND`

    Route every named net and resolve all clearance, unconnected-item, and board-
    outline findings. Save the finished board as
    `artifacts/max3485-rs485.kicad_pcb`; it must pass KiCad DRC with no errors
    or warnings.
    Preserve `artifacts/max3485-rs485.kicad_pro` byte-for-byte; it is the protected project-rules file.

    Use routed copper at least 0.25 mm wide on every named net.
