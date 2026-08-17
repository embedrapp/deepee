# SN65HVD230 CAN transceiver: PCB

    A 3.3 V node needs a high-speed CAN interface with selectable 120 Ω termination, a defined slope-control resistor, local decoupling, and logic/bus connectors.

    Create a two-layer PCB from the empty starter using the connection table below. Keep a 60 mm × 40 mm rectangular outline and use the exact references,
    values, footprints, and pin nets below:

    - `U1` = `SN65HVD230`; footprint `Package_SO:SOIC-8_3.9x4.9mm_P1.27mm`: pin 1 → `CAN_TX`, pin 2 → `GND`, pin 3 → `3V3`, pin 4 → `CAN_RX`, pin 5 → `VREF`, pin 6 → `CANL`, pin 7 → `CANH`, pin 8 → `RS`
- `R1` = `120R`; footprint `Resistor_SMD:R_0603_1608Metric`: pin 1 → `CANH`, pin 2 → `CANL`
- `R2` = `10k`; footprint `Resistor_SMD:R_0603_1608Metric`: pin 1 → `RS`, pin 2 → `GND`
- `C1` = `100nF`; footprint `Capacitor_SMD:C_0603_1608Metric`: pin 1 → `3V3`, pin 2 → `GND`
- `J1` = `Conn_01x05`; footprint `Connector_PinHeader_2.54mm:PinHeader_1x05_P2.54mm_Vertical`: pin 1 → `3V3`, pin 2 → `GND`, pin 3 → `CAN_TX`, pin 4 → `CAN_RX`, pin 5 → `VREF`
- `J2` = `Conn_01x03`; footprint `TerminalBlock_RND:TerminalBlock_RND_205-00288_1x03_P5.08mm_Horizontal`: pin 1 → `CANH`, pin 2 → `CANL`, pin 3 → `GND`

    Route every named net and resolve all clearance, unconnected-item, and board-
    outline findings. Save the finished board as
    `artifacts/sn65hvd230-can.kicad_pcb`; it must pass KiCad DRC with no errors
    or warnings.
    Preserve `artifacts/sn65hvd230-can.kicad_pro` byte-for-byte; it is the protected project-rules file.

    Use routed copper at least 0.25 mm wide on every named net.
