# BMP280 environmental sensor: PCB

    A compact pressure sensor must operate in I²C mode from 3.3 V, remain deselected from SPI mode, and expose power and I²C through a four-pin connector.

    Complete and repair the supplied two-layer layout. All components are present, but the copper is unfinished and the board cannot be manufactured as-is. Keep a 60 mm × 40 mm rectangular outline and use the exact references,
    values, footprints, and pin nets below:

    - `U1` = `BMP280`: pin 1 → `GND`, pin 2 → `3V3`, pin 3 → `SDA`, pin 4 → `SCL`, pin 5 → `ADDR`, pin 6 → `3V3`, pin 7 → `GND`, pin 8 → `3V3`
- `R1` = `4.7k`: pin 1 → `3V3`, pin 2 → `SDA`
- `R2` = `4.7k`: pin 1 → `3V3`, pin 2 → `SCL`
- `R3` = `0R`: pin 1 → `ADDR`, pin 2 → `GND`
- `C1` = `100nF`: pin 1 → `3V3`, pin 2 → `GND`
- `C2` = `1uF`: pin 1 → `3V3`, pin 2 → `GND`
- `J1` = `Conn_01x04`: pin 1 → `3V3`, pin 2 → `GND`, pin 3 → `SDA`, pin 4 → `SCL`

    Route every named net and resolve all clearance, unconnected-item, and board-
    outline findings. Save the finished board as
    `artifacts/bmp280-environment-sensor.kicad_pcb`; it must pass KiCad DRC with no errors
    or warnings.

Use routed copper at least 0.25 mm wide on every named net.
