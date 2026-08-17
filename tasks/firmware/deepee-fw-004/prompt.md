# Implement the Modbus RTU CRC contract

Complete `src/modbus_crc.c` using the protected API.

Implement the Modbus serial-line CRC-16 algorithm with initial value `0xFFFF`, reflected polynomial `0xA001`, and least-significant-bit-first processing. `modbus_rtu_append_crc` must append the low CRC byte first and the high byte second, returning the new frame length or zero when the buffer/capacity is invalid. `modbus_rtu_frame_valid` must reject frames shorter than one payload byte plus two CRC bytes.

The canonical request payload `01 03 00 00 00 0A` produces CRC value `0xCDC5` and is transmitted with bytes `C5 CD`.

Do not change `modbus_crc.h`, `main.cpp`, or `platformio.ini`. Submit the completed C file in place and keep it compatible with the ESP32-S2 build.
