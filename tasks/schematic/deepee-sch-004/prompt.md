# ADS1115 four-channel analog input: schematic

    A sensor hub needs four single-ended analog inputs, an address strap, an alert output, local decoupling, and a 3.3 V I²C host connection.

    Audit the supplied schematic, correct the show-stopping electrical mistakes, and preserve the stated interface. Use the exact references, values, footprints, and nets below:

    - `U1` = `ADS1115IDGS`: pin 1 → `GND`, pin 2 → `ALERT`, pin 3 → `GND`, pin 4 → `AIN0`, pin 5 → `AIN1`, pin 6 → `AIN2`, pin 7 → `AIN3`, pin 8 → `3V3`, pin 9 → `SDA`, pin 10 → `SCL`
- `R1` = `4.7k`: pin 1 → `3V3`, pin 2 → `SDA`
- `R2` = `4.7k`: pin 1 → `3V3`, pin 2 → `SCL`
- `R3` = `10k`: pin 1 → `3V3`, pin 2 → `ALERT`
- `C1` = `100nF`: pin 1 → `3V3`, pin 2 → `GND`
- `J1` = `Conn_01x10`: pin 1 → `3V3`, pin 2 → `GND`, pin 3 → `SDA`, pin 4 → `SCL`, pin 5 → `ALERT`, pin 6 → `AIN0`, pin 7 → `AIN1`, pin 8 → `AIN2`, pin 9 → `AIN3`, pin 10 → `GND`

    Use explicit labels for every named net. The finished schematic must export a
    netlist matching this connection table and pass KiCad ERC with no errors or
    warnings. Save it as `artifacts/ads1115-analog-input.kicad_sch`.
