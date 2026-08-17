# INA219 current-monitor interface: PCB

    A 3.3 V controller must measure a high-side supply rail while exposing the bus voltage, shunt path, and I²C interface on one service connector.

    Complete and repair the supplied two-layer layout. All components are present, but the copper is unfinished and the board cannot be manufactured as-is. Keep a 60 mm × 40 mm rectangular outline and use the exact references,
    values, footprints, and pin nets below:

    - `U1` = `INA219AxD`: pin 1 → `GND`, pin 2 → `GND`, pin 3 → `SDA`, pin 4 → `SCL`, pin 5 → `3V3`, pin 6 → `GND`, pin 7 → `VIN_OUT`, pin 8 → `VIN_IN`
- `R1` = `0.1R`: pin 1 → `VIN_IN`, pin 2 → `VIN_OUT`
- `R2` = `4.7k`: pin 1 → `3V3`, pin 2 → `SDA`
- `R3` = `4.7k`: pin 1 → `3V3`, pin 2 → `SCL`
- `C1` = `100nF`: pin 1 → `3V3`, pin 2 → `GND`
- `J1` = `Conn_01x06`: pin 1 → `VIN_IN`, pin 2 → `VIN_OUT`, pin 3 → `3V3`, pin 4 → `GND`, pin 5 → `SDA`, pin 6 → `SCL`

    Route every named net and resolve all clearance, unconnected-item, and board-
    outline findings. Save the finished board as
    `artifacts/ina219-current-monitor.kicad_pcb`; it must pass KiCad DRC with no errors
    or warnings.

Use routed copper at least 0.25 mm wide on every named net.
