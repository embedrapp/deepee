# AP2112K 3.3 V regulator: PCB

    A 5 V accessory rail must be regulated to 3.3 V with the regulator enabled whenever input power is present and with local input/output capacitors.

    Complete and repair the supplied two-layer layout. All components are present, but the copper is unfinished and the board cannot be manufactured as-is. Keep a 60 mm × 40 mm rectangular outline and use the exact references,
    values, footprints, and pin nets below:

    - `U1` = `AP2112K-3.3`: pin 1 → `VIN`, pin 2 → `GND`, pin 3 → `VIN`, pin 5 → `3V3`
- `C1` = `1uF`: pin 1 → `VIN`, pin 2 → `GND`
- `C2` = `1uF`: pin 1 → `3V3`, pin 2 → `GND`
- `R1` = `100k`: pin 1 → `VIN`, pin 2 → `GND`
- `J1` = `Conn_01x03`: pin 1 → `VIN`, pin 2 → `GND`, pin 3 → `3V3`

    Route every named net and resolve all clearance, unconnected-item, and board-
    outline findings. Save the finished board as
    `artifacts/ap2112-3v3-regulator.kicad_pcb`; it must pass KiCad DRC with no errors
    or warnings.

Use routed copper at least 0.25 mm wide on every named net.
