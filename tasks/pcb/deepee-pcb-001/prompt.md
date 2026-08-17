# Finish routing the nRF24L01 adapter

The supplied KiCad 10 board is a compact adaptation of a real open-source nRF24L01 breakout. Placement, the 30 mm × 25 mm outline, footprints, references, values, and pad nets are fixed.

The enforced component identities are:

- `J1` = `Conn_01x08`; footprint `Connector_PinHeader_2.54mm:PinHeader_1x08_P2.54mm_Vertical`;
- `J2` = `nRF24L01_Module`; footprint `Connector_PinSocket_2.54mm:PinSocket_2x04_P2.54mm_Vertical`;
- `C1` = `10uF`; footprint `Capacitor_SMD:C_0805_2012Metric`;
- `C2` = `100nF`; footprint `Capacitor_SMD:C_0603_1608Metric`.

Power, `CE`, and `CSN` have starter routing. Complete every remaining connection: `SCK`, `MOSI`, `MISO`, and `IRQ`. You may edit or reroute existing copper and use either copper layer, but do not change the board outline or component contract.

Submit the completed board at `artifacts/nrf24-adapter.kicad_pcb`. The task passes only when all eight nets have copper connectivity and KiCad DRC reports no errors or warnings. Trace geometry is not compared with a golden layout.

Use routed copper at least 0.25 mm wide on every named net.
