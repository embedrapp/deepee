# microSD SPI adapter: PCB

    A 3.3 V data logger needs a microSD socket wired for SPI mode with defined pull-ups, local bulk/high-frequency decoupling, and a six-pin controller header.

    Create a two-layer PCB from the empty starter using the connection table below. Keep a 60 mm × 40 mm rectangular outline and use the exact references,
    values, footprints, and pin nets below:

    - `J1` = `Micro_SD_Card`; footprint `Connector_Card:microSD_HC_Hirose_DM3AT-SF-PEJM5`: pin 1 → `DAT2`, pin 2 → `SD_CS`, pin 3 → `MOSI`, pin 4 → `3V3`, pin 5 → `SCK`, pin 6 → `GND`, pin 7 → `MISO`, pin 8 → `DAT1`, pin SH → `GND`
- `R1` = `47k`; footprint `Resistor_SMD:R_0603_1608Metric`: pin 1 → `3V3`, pin 2 → `SD_CS`
- `R2` = `47k`; footprint `Resistor_SMD:R_0603_1608Metric`: pin 1 → `3V3`, pin 2 → `DAT1`
- `R3` = `47k`; footprint `Resistor_SMD:R_0603_1608Metric`: pin 1 → `3V3`, pin 2 → `DAT2`
- `C1` = `100nF`; footprint `Capacitor_SMD:C_0603_1608Metric`: pin 1 → `3V3`, pin 2 → `GND`
- `C2` = `10uF`; footprint `Capacitor_SMD:C_0805_2012Metric`: pin 1 → `3V3`, pin 2 → `GND`
- `J2` = `Conn_01x06`; footprint `Connector_PinHeader_2.54mm:PinHeader_1x06_P2.54mm_Vertical`: pin 1 → `3V3`, pin 2 → `GND`, pin 3 → `SD_CS`, pin 4 → `MOSI`, pin 5 → `MISO`, pin 6 → `SCK`

    Route every named net and resolve all clearance, unconnected-item, and board-
    outline findings. Save the finished board as
    `artifacts/microsd-spi-adapter.kicad_pcb`; it must pass KiCad DRC with no errors
    or warnings.
    Preserve `artifacts/microsd-spi-adapter.kicad_pro` byte-for-byte; it is the protected project-rules file.

    Use routed copper at least 0.25 mm wide on every named net.
