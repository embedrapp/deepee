# BMP280 environmental sensor: schematic

    A compact pressure sensor must operate in I²C mode from 3.3 V, remain deselected from SPI mode, and expose power and I²C through a four-pin connector.

    Audit the supplied schematic, correct the show-stopping electrical mistakes, and preserve the stated interface. Use the exact references, values, footprints, and nets below:

    - `U1` = `BMP280`: pin 1 → `GND`, pin 2 → `3V3`, pin 3 → `SDA`, pin 4 → `SCL`, pin 5 → `ADDR`, pin 6 → `3V3`, pin 7 → `GND`, pin 8 → `3V3`
- `R1` = `4.7k`: pin 1 → `3V3`, pin 2 → `SDA`
- `R2` = `4.7k`: pin 1 → `3V3`, pin 2 → `SCL`
- `R3` = `0R`: pin 1 → `ADDR`, pin 2 → `GND`
- `C1` = `100nF`: pin 1 → `3V3`, pin 2 → `GND`
- `C2` = `1uF`: pin 1 → `3V3`, pin 2 → `GND`
- `J1` = `Conn_01x04`: pin 1 → `3V3`, pin 2 → `GND`, pin 3 → `SDA`, pin 4 → `SCL`

    Use explicit labels for every named net. The finished schematic must export a
    netlist matching this connection table and pass KiCad ERC with no errors or
    warnings. Save it as `artifacts/bmp280-environment-sensor.kicad_sch`.
