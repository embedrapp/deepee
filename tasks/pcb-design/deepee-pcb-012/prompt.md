# NE555 astable oscillator: PCB

    A production fixture needs a roughly 1 kHz free-running oscillator from 5 V, with reset held active, a timing RC network, control-pin bypassing, supply decoupling, and a three-pin output header.

    Create a two-layer PCB from the empty starter using the connection table below. Keep a 60 mm × 40 mm rectangular outline and use the exact references,
    values, footprints, and pin nets below:

    - `U1` = `NE555D`: pin 1 → `GND`, pin 2 → `TIMING`, pin 3 → `OUT`, pin 4 → `5V`, pin 5 → `CTRL`, pin 6 → `TIMING`, pin 7 → `DISCHARGE`, pin 8 → `5V`
- `R1` = `4.7k`: pin 1 → `5V`, pin 2 → `DISCHARGE`
- `R2` = `68k`: pin 1 → `DISCHARGE`, pin 2 → `TIMING`
- `C1` = `10nF`: pin 1 → `TIMING`, pin 2 → `GND`
- `C2` = `10nF`: pin 1 → `CTRL`, pin 2 → `GND`
- `C3` = `100nF`: pin 1 → `5V`, pin 2 → `GND`
- `J1` = `Conn_01x03`: pin 1 → `5V`, pin 2 → `GND`, pin 3 → `OUT`

    Route every named net and resolve all clearance, unconnected-item, and board-
    outline findings. Save the finished board as
    `artifacts/ne555-astable.kicad_pcb`; it must pass KiCad DRC with no errors
    or warnings.
