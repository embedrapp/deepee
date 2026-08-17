# BMP280 environmental sensor: schematic

    A compact pressure sensor must operate in I²C mode from 3.3 V, remain deselected from SPI mode, and expose power and I²C through a four-pin connector.

    Audit the supplied schematic, correct the show-stopping electrical mistakes, and preserve the stated interface. Use the exact references, values, footprints, and nets below:

    - `U1` = `BMP280`; symbol `Sensor_Pressure:BMP280`; footprint `Package_LGA:Bosch_LGA-8_2x2.5mm_P0.65mm_ClockwisePinNumbering`: pin 1 → `GND`, pin 2 → `3V3`, pin 3 → `SDA`, pin 4 → `SCL`, pin 5 → `ADDR`, pin 6 → `3V3`, pin 7 → `GND`, pin 8 → `3V3`
- `R1` = `4.7k`; symbol `Device:R`; footprint `Resistor_SMD:R_0603_1608Metric`: pin 1 → `3V3`, pin 2 → `SDA`
- `R2` = `4.7k`; symbol `Device:R`; footprint `Resistor_SMD:R_0603_1608Metric`: pin 1 → `3V3`, pin 2 → `SCL`
- `R3` = `0R`; symbol `Device:R`; footprint `Resistor_SMD:R_0603_1608Metric`: pin 1 → `ADDR`, pin 2 → `GND`
- `C1` = `100nF`; symbol `Device:C`; footprint `Capacitor_SMD:C_0603_1608Metric`: pin 1 → `3V3`, pin 2 → `GND`
- `C2` = `1uF`; symbol `Device:C`; footprint `Capacitor_SMD:C_0603_1608Metric`: pin 1 → `3V3`, pin 2 → `GND`
- `J1` = `Conn_01x04`; symbol `Connector_Generic:Conn_01x04`; footprint `Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical`: pin 1 → `3V3`, pin 2 → `GND`, pin 3 → `SDA`, pin 4 → `SCL`

    Use explicit labels for every named net. The finished schematic must export a
    netlist matching this connection table and pass KiCad ERC with no errors or
    warnings. Save it as `artifacts/bmp280-environment-sensor.kicad_sch`.
    Preserve `artifacts/bmp280-environment-sensor.kicad_pro` byte-for-byte; it is the protected project-rules file.
