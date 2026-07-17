# Repair the swapped power pins

Review `artifacts/power-input.kicad_sch`. The fixed circuit is:

- `U1`, `Test:Test_Symbol_GND`: pin 1 (`VCC`) must be on `+5V`; pin 2 (`GND`) must be on `GND`;
- `R1`, `Device:R`, value `1k`: pin 1 on `+5V`, pin 2 on `GND`;
- both rails remain explicitly driven by their existing power flags.

The symbol orientation is wrong in the starter and swaps the intended power pins. Repair the schematic without adding, deleting, renaming, or changing the value of `U1` or `R1`.

Submit the repaired KiCad 10 schematic at the same path. It must match the pin-to-net contract and pass ERC with no errors or warnings.
