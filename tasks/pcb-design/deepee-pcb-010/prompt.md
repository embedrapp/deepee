# PCA9306 I²C level shifter: PCB

    A 1.8 V processor must communicate with a 3.3 V I²C sensor bus using a pass-FET level translator, pull-ups on both sides, a correctly biased enable/reference network, and decoupling.

    Create a two-layer PCB from the empty starter using the connection table below. Keep a 60 mm × 40 mm rectangular outline and use the exact references,
    values, footprints, and pin nets below:

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

    Route every named net and resolve all clearance, unconnected-item, and board-
    outline findings. Save the finished board as
    `artifacts/pca9306-i2c-level-shifter.kicad_pcb`; it must pass KiCad DRC with no errors
    or warnings.
