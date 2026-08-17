# SN65HVD230 CAN transceiver: schematic

    A 3.3 V node needs a high-speed CAN interface with selectable 120 Ω termination, a defined slope-control resistor, local decoupling, and logic/bus connectors.

    Create the schematic from the empty starter and implement the complete electrical interface. Use the exact references, values, footprints, and nets below:

    - `U1` = `SN65HVD230`: pin 1 → `CAN_TX`, pin 2 → `GND`, pin 3 → `3V3`, pin 4 → `CAN_RX`, pin 5 → `VREF`, pin 6 → `CANL`, pin 7 → `CANH`, pin 8 → `RS`
- `R1` = `120R`: pin 1 → `CANH`, pin 2 → `CANL`
- `R2` = `10k`: pin 1 → `RS`, pin 2 → `GND`
- `C1` = `100nF`: pin 1 → `3V3`, pin 2 → `GND`
- `J1` = `Conn_01x05`: pin 1 → `3V3`, pin 2 → `GND`, pin 3 → `CAN_TX`, pin 4 → `CAN_RX`, pin 5 → `VREF`
- `J2` = `Conn_01x03`: pin 1 → `CANH`, pin 2 → `CANL`, pin 3 → `GND`

    Use explicit labels for every named net. The finished schematic must export a
    netlist matching this connection table and pass KiCad ERC with no errors or
    warnings. Save it as `artifacts/sn65hvd230-can.kicad_sch`.
