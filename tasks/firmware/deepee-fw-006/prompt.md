# Decode INA219 measurement registers

Finish `src/ina219_decode.c` for the current-monitor telemetry path.

The shunt-voltage register is a signed 16-bit two's-complement value at
10 µV per bit. In the bus-voltage register, bits 15:3 hold an unsigned
measurement at 4 mV per bit, bit 1 is the conversion-ready flag, and
bit 0 is the math-overflow flag. Return voltages in microvolts and
preserve both flags.

Reject a null output pointer. Do not change the header, `main.cpp`, or
`platformio.ini`. Submit the completed C file in place; it must pass the
native tests and the ESP32-S2 build.
