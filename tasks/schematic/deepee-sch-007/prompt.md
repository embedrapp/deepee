# USB-C 5 V sink input: schematic

    A USB 2.0 peripheral needs a Type-C receptacle in sink mode, independent Rd resistors on CC1 and CC2, a protected 5 V rail, and D+/D− continuity to its system header.

    Audit the supplied schematic, correct the show-stopping electrical mistakes, and preserve the stated interface. Use the exact references, values, footprints, and nets below:

    - `J1` = `USB_C_Receptacle_USB2.0_16P`; symbol `Connector:USB_C_Receptacle_USB2.0_16P`; footprint `Connector_USB:USB_C_Receptacle_GCT_USB4105-xx-A_16P_TopMnt_Horizontal`: pin A1 → `GND`, pin A4 → `VBUS`, pin A5 → `CC1`, pin A6 → `USB_DP`, pin A7 → `USB_DM`, pin A9 → `VBUS`, pin A12 → `GND`, pin B1 → `GND`, pin B4 → `VBUS`, pin B5 → `CC2`, pin B6 → `USB_DP`, pin B7 → `USB_DM`, pin B9 → `VBUS`, pin B12 → `GND`, pin SH → `GND`
- `R1` = `5.1k`; symbol `Device:R`; footprint `Resistor_SMD:R_0603_1608Metric`: pin 1 → `CC1`, pin 2 → `GND`
- `R2` = `5.1k`; symbol `Device:R`; footprint `Resistor_SMD:R_0603_1608Metric`: pin 1 → `CC2`, pin 2 → `GND`
- `F1` = `500mA`; symbol `Device:Fuse`; footprint `Fuse:Fuse_1206_3216Metric`: pin 1 → `VBUS`, pin 2 → `5V`
- `C1` = `10uF`; symbol `Device:C`; footprint `Capacitor_SMD:C_0805_2012Metric`: pin 1 → `5V`, pin 2 → `GND`
- `J2` = `Conn_01x04`; symbol `Connector_Generic:Conn_01x04`; footprint `Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical`: pin 1 → `5V`, pin 2 → `GND`, pin 3 → `USB_DP`, pin 4 → `USB_DM`

    Use explicit labels for every named net. The finished schematic must export a
    netlist matching this connection table and pass KiCad ERC with no errors or
    warnings. Save it as `artifacts/usb-c-5v-sink.kicad_sch`.
    Preserve `artifacts/usb-c-5v-sink.kicad_pro` byte-for-byte; it is the protected project-rules file.
