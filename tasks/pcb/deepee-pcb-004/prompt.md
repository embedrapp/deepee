# ADS1115 four-channel analog input: PCB

    A sensor hub needs four single-ended analog inputs, an address strap, an alert output, local decoupling, and a 3.3 V I²C host connection.

    Complete and repair the supplied two-layer layout. All components are present, but the copper is unfinished and the board cannot be manufactured as-is. Keep a 60 mm × 40 mm rectangular outline and use the exact references,
    values, footprints, and pin nets below:

    - `U1` = `ADS1115IDGS`: pin 1 → `GND`, pin 2 → `ALERT`, pin 3 → `GND`, pin 4 → `AIN0`, pin 5 → `AIN1`, pin 6 → `AIN2`, pin 7 → `AIN3`, pin 8 → `3V3`, pin 9 → `SDA`, pin 10 → `SCL`
- `R1` = `4.7k`: pin 1 → `3V3`, pin 2 → `SDA`
- `R2` = `4.7k`: pin 1 → `3V3`, pin 2 → `SCL`
- `R3` = `10k`: pin 1 → `3V3`, pin 2 → `ALERT`
- `C1` = `100nF`: pin 1 → `3V3`, pin 2 → `GND`
- `J1` = `Conn_01x10`: pin 1 → `3V3`, pin 2 → `GND`, pin 3 → `SDA`, pin 4 → `SCL`, pin 5 → `ALERT`, pin 6 → `AIN0`, pin 7 → `AIN1`, pin 8 → `AIN2`, pin 9 → `AIN3`, pin 10 → `GND`

    Route every named net and resolve all clearance, unconnected-item, and board-
    outline findings. Save the finished board as
    `artifacts/ads1115-analog-input.kicad_pcb`; it must pass KiCad DRC with no errors
    or warnings.

Use routed copper at least 0.25 mm wide on every named net.
