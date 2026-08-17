# PCA9306 I²C level shifter: schematic

    A 1.8 V processor must communicate with a 3.3 V I²C sensor bus using a pass-FET level translator, pull-ups on both sides, a correctly biased enable/reference network, and decoupling.

    Create the schematic from the empty starter and implement the complete electrical interface. Use the exact references, values, footprints, and nets below:

    - `U1` = `PCA9306D`; symbol `Interface:PCA9306D`; footprint `Package_SO:TSSOP-8_3x3mm_P0.65mm`: pin 1 → `GND`, pin 2 → `1V8`, pin 3 → `SCL_1V8`, pin 4 → `SDA_1V8`, pin 5 → `SDA_3V3`, pin 6 → `SCL_3V3`, pin 7 → `3V3`, pin 8 → `ENABLE`
- `R1` = `4.7k`; symbol `Device:R`; footprint `Resistor_SMD:R_0603_1608Metric`: pin 1 → `1V8`, pin 2 → `SDA_1V8`
- `R2` = `4.7k`; symbol `Device:R`; footprint `Resistor_SMD:R_0603_1608Metric`: pin 1 → `1V8`, pin 2 → `SCL_1V8`
- `R3` = `4.7k`; symbol `Device:R`; footprint `Resistor_SMD:R_0603_1608Metric`: pin 1 → `3V3`, pin 2 → `SDA_3V3`
- `R4` = `4.7k`; symbol `Device:R`; footprint `Resistor_SMD:R_0603_1608Metric`: pin 1 → `3V3`, pin 2 → `SCL_3V3`
- `R5` = `200k`; symbol `Device:R`; footprint `Resistor_SMD:R_0603_1608Metric`: pin 1 → `ENABLE`, pin 2 → `3V3`
- `C1` = `100nF`; symbol `Device:C`; footprint `Capacitor_SMD:C_0603_1608Metric`: pin 1 → `1V8`, pin 2 → `GND`
- `C2` = `100nF`; symbol `Device:C`; footprint `Capacitor_SMD:C_0603_1608Metric`: pin 1 → `3V3`, pin 2 → `GND`
- `J1` = `Conn_01x04`; symbol `Connector_Generic:Conn_01x04`; footprint `Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical`: pin 1 → `1V8`, pin 2 → `GND`, pin 3 → `SDA_1V8`, pin 4 → `SCL_1V8`
- `J2` = `Conn_01x04`; symbol `Connector_Generic:Conn_01x04`; footprint `Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical`: pin 1 → `3V3`, pin 2 → `GND`, pin 3 → `SDA_3V3`, pin 4 → `SCL_3V3`

    Use explicit labels for every named net. The finished schematic must export a
    netlist matching this connection table and pass KiCad ERC with no errors or
    warnings. Save it as `artifacts/pca9306-i2c-level-shifter.kicad_sch`.
    Preserve `artifacts/pca9306-i2c-level-shifter.kicad_pro` byte-for-byte; it is the protected project-rules file.
