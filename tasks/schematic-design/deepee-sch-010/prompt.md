# PCA9306 I²C level shifter: schematic

    A 1.8 V processor must communicate with a 3.3 V I²C sensor bus using a pass-FET level translator, pull-ups on both sides, a correctly biased enable/reference network, and decoupling.

    Create the schematic from the empty starter and implement the complete electrical interface. Use the exact references, values, footprints, and nets below:

    - `U1` = `PCA9306D`: pin 1 → `GND`, pin 2 → `1V8`, pin 3 → `SCL_1V8`, pin 4 → `SDA_1V8`, pin 5 → `SDA_3V3`, pin 6 → `SCL_3V3`, pin 7 → `3V3`, pin 8 → `ENABLE`
- `R1` = `4.7k`: pin 1 → `1V8`, pin 2 → `SDA_1V8`
- `R2` = `4.7k`: pin 1 → `1V8`, pin 2 → `SCL_1V8`
- `R3` = `4.7k`: pin 1 → `3V3`, pin 2 → `SDA_3V3`
- `R4` = `4.7k`: pin 1 → `3V3`, pin 2 → `SCL_3V3`
- `R5` = `200k`: pin 1 → `ENABLE`, pin 2 → `3V3`
- `C1` = `100nF`: pin 1 → `1V8`, pin 2 → `GND`
- `C2` = `100nF`: pin 1 → `3V3`, pin 2 → `GND`
- `J1` = `Conn_01x04`: pin 1 → `1V8`, pin 2 → `GND`, pin 3 → `SDA_1V8`, pin 4 → `SCL_1V8`
- `J2` = `Conn_01x04`: pin 1 → `3V3`, pin 2 → `GND`, pin 3 → `SDA_3V3`, pin 4 → `SCL_3V3`

    Use explicit labels for every named net. The finished schematic must export a
    netlist matching this connection table and pass KiCad ERC with no errors or
    warnings. Save it as `artifacts/pca9306-i2c-level-shifter.kicad_sch`.
