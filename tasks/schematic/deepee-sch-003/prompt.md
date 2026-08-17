# INA219 current-monitor interface: schematic

    A 3.3 V controller must measure a high-side supply rail while exposing the bus voltage, shunt path, and I²C interface on one service connector.

    Audit the supplied schematic, correct the show-stopping electrical mistakes, and preserve the stated interface. Use the exact references, values, footprints, and nets below:

    - `U1` = `INA219AxD`: pin 1 → `GND`, pin 2 → `GND`, pin 3 → `SDA`, pin 4 → `SCL`, pin 5 → `3V3`, pin 6 → `GND`, pin 7 → `VIN_OUT`, pin 8 → `VIN_IN`
- `R1` = `0.1R`: pin 1 → `VIN_IN`, pin 2 → `VIN_OUT`
- `R2` = `4.7k`: pin 1 → `3V3`, pin 2 → `SDA`
- `R3` = `4.7k`: pin 1 → `3V3`, pin 2 → `SCL`
- `C1` = `100nF`: pin 1 → `3V3`, pin 2 → `GND`
- `J1` = `Conn_01x06`: pin 1 → `VIN_IN`, pin 2 → `VIN_OUT`, pin 3 → `3V3`, pin 4 → `GND`, pin 5 → `SDA`, pin 6 → `SCL`

    Use explicit labels for every named net. The finished schematic must export a
    netlist matching this connection table and pass KiCad ERC with no errors or
    warnings. Save it as `artifacts/ina219-current-monitor.kicad_sch`.
