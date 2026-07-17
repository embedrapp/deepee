# Finish routing the nRF24L01 adapter

The supplied KiCad 10 board is a compact adaptation of a real open-source nRF24L01 breakout. Placement, the 30 mm × 25 mm outline, footprints, references, values, and pad nets are fixed.

Power, `CE`, and `CSN` have starter routing. Complete every remaining connection: `SCK`, `MOSI`, `MISO`, and `IRQ`. You may edit or reroute existing copper and use either copper layer, but do not change the board outline or component contract.

Submit the completed board at `artifacts/nrf24-adapter.kicad_pcb`. The task passes only when all eight nets have copper connectivity and KiCad DRC reports no errors or warnings. Trace geometry is not compared with a golden layout.
