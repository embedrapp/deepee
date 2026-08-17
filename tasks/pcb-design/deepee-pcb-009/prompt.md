# SN65HVD230 CAN transceiver: PCB

    A 3.3 V node needs a high-speed CAN interface with selectable 120 Ω termination, a defined slope-control resistor, local decoupling, and logic/bus connectors.

    Create a two-layer PCB from the empty starter using the connection table below. Keep a 60 mm × 40 mm rectangular outline and use the exact references,
    values, footprints, and pin nets below:

    - `U1` = `SN65HVD230`: pin 1 → `CAN_TX`, pin 2 → `GND`, pin 3 → `3V3`, pin 4 → `CAN_RX`, pin 5 → `VREF`, pin 6 → `CANL`, pin 7 → `CANH`, pin 8 → `RS`
- `R1` = `120R`: pin 1 → `CANH`, pin 2 → `CANL`
- `R2` = `10k`: pin 1 → `RS`, pin 2 → `GND`
- `C1` = `100nF`: pin 1 → `3V3`, pin 2 → `GND`
- `J1` = `Conn_01x05`: pin 1 → `3V3`, pin 2 → `GND`, pin 3 → `CAN_TX`, pin 4 → `CAN_RX`, pin 5 → `VREF`
- `J2` = `Conn_01x03`: pin 1 → `CANH`, pin 2 → `CANL`, pin 3 → `GND`

    Route every named net and resolve all clearance, unconnected-item, and board-
    outline findings. Save the finished board as
    `artifacts/sn65hvd230-can.kicad_pcb`; it must pass KiCad DRC with no errors
    or warnings.
