# Implement SHT3x frame validation and conversion

Complete `src/sht3x_decode.c` using the protected API and the SHT3x measurement-frame contract.

Each six-byte frame is `temperature MSB`, `temperature LSB`, temperature CRC, `humidity MSB`, `humidity LSB`, humidity CRC. Implement the Sensirion CRC-8 with polynomial `0x31`, initialization `0xFF`, no reflection, and no final XOR. Reject a frame if either two-byte word has the wrong CRC.

For a valid frame, round to the nearest output unit using:

- temperature in milli-degrees Celsius: `-45000 + 175000 * raw / 65535`;
- relative humidity in milli-percent: `100000 * raw / 65535`.

Do not change `sht3x_decode.h`, `main.cpp`, or `platformio.ini`. Submit the completed C file in place and keep it compatible with the ESP32-S2 target build.
