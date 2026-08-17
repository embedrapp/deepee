# NE555 astable oscillator: schematic

    A production fixture needs a roughly 1 kHz free-running oscillator from 5 V, with reset held active, a timing RC network, control-pin bypassing, supply decoupling, and a three-pin output header.

    Create the schematic from the empty starter and implement the complete electrical interface. Use the exact references, values, footprints, and nets below:

    - `U1` = `NE555D`: pin 1 → `GND`, pin 2 → `TIMING`, pin 3 → `OUT`, pin 4 → `5V`, pin 5 → `CTRL`, pin 6 → `TIMING`, pin 7 → `DISCHARGE`, pin 8 → `5V`
- `R1` = `4.7k`: pin 1 → `5V`, pin 2 → `DISCHARGE`
- `R2` = `68k`: pin 1 → `DISCHARGE`, pin 2 → `TIMING`
- `C1` = `10nF`: pin 1 → `TIMING`, pin 2 → `GND`
- `C2` = `10nF`: pin 1 → `CTRL`, pin 2 → `GND`
- `C3` = `100nF`: pin 1 → `5V`, pin 2 → `GND`
- `J1` = `Conn_01x03`: pin 1 → `5V`, pin 2 → `GND`, pin 3 → `OUT`

    Use explicit labels for every named net. The finished schematic must export a
    netlist matching this connection table and pass KiCad ERC with no errors or
    warnings. Save it as `artifacts/ne555-astable.kicad_sch`.
