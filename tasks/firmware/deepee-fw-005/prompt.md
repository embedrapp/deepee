# Decode the MCP9808 ambient-temperature register

Complete `src/mcp9808_decode.c` using the protected API.

The 16-bit ambient-temperature register contains three alert flags in bits 15, 14, and 13; a sign bit in bit 12; and twelve fractional temperature bits in bits 11 through 0. Decode the lower 13 bits as a signed fixed-point value with 1/16 °C resolution. Return temperature in micro-degrees Celsius, where one register step is exactly `62500` µ°C, and preserve all three alert flags.

Examples:

- `0x0190` is +25.0000 °C;
- `0x1F60` is -10.0000 °C;
- flag bits do not change the decoded temperature.

Reject a null output pointer. Do not change `mcp9808_decode.h`, `main.cpp`, or `platformio.ini`. Submit the completed C file in place; it must pass native tests and the ESP32-S2 build.
