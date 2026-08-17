# AP2112K 3.3 V regulator: schematic

    A 5 V accessory rail must be regulated to 3.3 V with the regulator enabled whenever input power is present and with local input/output capacitors.

    Audit the supplied schematic, correct the show-stopping electrical mistakes, and preserve the stated interface. Use the exact references, values, footprints, and nets below:

    - `U1` = `AP2112K-3.3`; symbol `Regulator_Linear:AP2112K-3.3`; footprint `Package_TO_SOT_SMD:SOT-23-5`: pin 1 → `VIN`, pin 2 → `GND`, pin 3 → `VIN`, pin 5 → `3V3`
- `C1` = `1uF`; symbol `Device:C`; footprint `Capacitor_SMD:C_0805_2012Metric`: pin 1 → `VIN`, pin 2 → `GND`
- `C2` = `1uF`; symbol `Device:C`; footprint `Capacitor_SMD:C_0805_2012Metric`: pin 1 → `3V3`, pin 2 → `GND`
- `R1` = `100k`; symbol `Device:R`; footprint `Resistor_SMD:R_0603_1608Metric`: pin 1 → `VIN`, pin 2 → `GND`
- `J1` = `Conn_01x03`; symbol `Connector_Generic:Conn_01x03`; footprint `Connector_PinHeader_2.54mm:PinHeader_1x03_P2.54mm_Vertical`: pin 1 → `VIN`, pin 2 → `GND`, pin 3 → `3V3`

    Use explicit labels for every named net. The finished schematic must export a
    netlist matching this connection table and pass KiCad ERC with no errors or
    warnings. Save it as `artifacts/ap2112-3v3-regulator.kicad_sch`.
    Preserve `artifacts/ap2112-3v3-regulator.kicad_pro` byte-for-byte; it is the protected project-rules file.
