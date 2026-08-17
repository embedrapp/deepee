# USB-C 5 V sink input: PCB

    A USB 2.0 peripheral needs a Type-C receptacle in sink mode, independent Rd resistors on CC1 and CC2, a protected 5 V rail, and D+/D− continuity to its system header.

    Complete and repair the supplied two-layer layout. All components are present, but the copper is unfinished and the board cannot be manufactured as-is. Keep a 60 mm × 40 mm rectangular outline and use the exact references,
    values, footprints, and pin nets below:

    - `J1` = `USB_C_Receptacle_USB2.0_16P`: pin A1 → `GND`, pin A4 → `VBUS`, pin A5 → `CC1`, pin A6 → `USB_DP`, pin A7 → `USB_DM`, pin A9 → `VBUS`, pin A12 → `GND`, pin B1 → `GND`, pin B4 → `VBUS`, pin B5 → `CC2`, pin B6 → `USB_DP`, pin B7 → `USB_DM`, pin B9 → `VBUS`, pin B12 → `GND`, pin SH → `GND`
- `R1` = `5.1k`: pin 1 → `CC1`, pin 2 → `GND`
- `R2` = `5.1k`: pin 1 → `CC2`, pin 2 → `GND`
- `F1` = `500mA`: pin 1 → `VBUS`, pin 2 → `5V`
- `C1` = `10uF`: pin 1 → `5V`, pin 2 → `GND`
- `J2` = `Conn_01x04`: pin 1 → `5V`, pin 2 → `GND`, pin 3 → `USB_DP`, pin 4 → `USB_DM`

    Route every named net and resolve all clearance, unconnected-item, and board-
    outline findings. Save the finished board as
    `artifacts/usb-c-5v-sink.kicad_pcb`; it must pass KiCad DRC with no errors
    or warnings.

Use routed copper at least 0.25 mm wide on every named net. Keep the total routed lengths of `USB_DP` and `USB_DM` within 1.0 mm of each other.
