# microSD SPI adapter: schematic

    A 3.3 V data logger needs a microSD socket wired for SPI mode with defined pull-ups, local bulk/high-frequency decoupling, and a six-pin controller header.

    Create the schematic from the empty starter and implement the complete electrical interface. Use the exact references, values, footprints, and nets below:

    - `J1` = `Micro_SD_Card`; symbol `Connector:Micro_SD_Card`; footprint `Connector_Card:microSD_HC_Hirose_DM3AT-SF-PEJM5`: pin 1 → `DAT2`, pin 2 → `SD_CS`, pin 3 → `MOSI`, pin 4 → `3V3`, pin 5 → `SCK`, pin 6 → `GND`, pin 7 → `MISO`, pin 8 → `DAT1`, pin SH → `GND`
- `R1` = `47k`; symbol `Device:R`; footprint `Resistor_SMD:R_0603_1608Metric`: pin 1 → `3V3`, pin 2 → `SD_CS`
- `R2` = `47k`; symbol `Device:R`; footprint `Resistor_SMD:R_0603_1608Metric`: pin 1 → `3V3`, pin 2 → `DAT1`
- `R3` = `47k`; symbol `Device:R`; footprint `Resistor_SMD:R_0603_1608Metric`: pin 1 → `3V3`, pin 2 → `DAT2`
- `C1` = `100nF`; symbol `Device:C`; footprint `Capacitor_SMD:C_0603_1608Metric`: pin 1 → `3V3`, pin 2 → `GND`
- `C2` = `10uF`; symbol `Device:C`; footprint `Capacitor_SMD:C_0805_2012Metric`: pin 1 → `3V3`, pin 2 → `GND`
- `J2` = `Conn_01x06`; symbol `Connector_Generic:Conn_01x06`; footprint `Connector_PinHeader_2.54mm:PinHeader_1x06_P2.54mm_Vertical`: pin 1 → `3V3`, pin 2 → `GND`, pin 3 → `SD_CS`, pin 4 → `MOSI`, pin 5 → `MISO`, pin 6 → `SCK`

    Use explicit labels for every named net. The finished schematic must export a
    netlist matching this connection table and pass KiCad ERC with no errors or
    warnings. Save it as `artifacts/microsd-spi-adapter.kicad_sch`.
    Preserve `artifacts/microsd-spi-adapter.kicad_pro` byte-for-byte; it is the protected project-rules file.
