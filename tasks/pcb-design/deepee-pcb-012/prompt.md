# NE555 astable oscillator: PCB

    A production fixture needs a roughly 1 kHz free-running oscillator from 5 V, with reset held active, a timing RC network, control-pin bypassing, supply decoupling, and a three-pin output header.

    Create a two-layer PCB from the empty starter using the connection table below. Keep a 60 mm × 40 mm rectangular outline and use the exact references,
    values, footprints, and pin nets below:

    - `U1` = `NE555D`; footprint `Package_SO:SOIC-8_3.9x4.9mm_P1.27mm`: pin 1 → `GND`, pin 2 → `TIMING`, pin 3 → `OUT`, pin 4 → `5V`, pin 5 → `CTRL`, pin 6 → `TIMING`, pin 7 → `DISCHARGE`, pin 8 → `5V`
- `R1` = `4.7k`; footprint `Resistor_SMD:R_0603_1608Metric`: pin 1 → `5V`, pin 2 → `DISCHARGE`
- `R2` = `68k`; footprint `Resistor_SMD:R_0603_1608Metric`: pin 1 → `DISCHARGE`, pin 2 → `TIMING`
- `C1` = `10nF`; footprint `Capacitor_SMD:C_0603_1608Metric`: pin 1 → `TIMING`, pin 2 → `GND`
- `C2` = `10nF`; footprint `Capacitor_SMD:C_0603_1608Metric`: pin 1 → `CTRL`, pin 2 → `GND`
- `C3` = `100nF`; footprint `Capacitor_SMD:C_0603_1608Metric`: pin 1 → `5V`, pin 2 → `GND`
- `J1` = `Conn_01x03`; footprint `Connector_PinHeader_2.54mm:PinHeader_1x03_P2.54mm_Vertical`: pin 1 → `5V`, pin 2 → `GND`, pin 3 → `OUT`

    Route every named net and resolve all clearance, unconnected-item, and board-
    outline findings. Save the finished board as
    `artifacts/ne555-astable.kicad_pcb`; it must pass KiCad DRC with no errors
    or warnings.
    Preserve `artifacts/ne555-astable.kicad_pro` byte-for-byte; it is the protected project-rules file.

    Use routed copper at least 0.25 mm wide on every named net.
