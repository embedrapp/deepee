# Complete the ESP32-S2 I²C recovery policy

This PlatformIO project reproduces the operating conditions from a real ESP32-S2 failure report: a 400 kHz bus on SDA GPIO 8 and SCL GPIO 9, a PCA9547 mux at `0x71`, and an optional downstream device at `0x60` that can be absent.

Complete `src/i2c_recovery.c` using the protected API:

- status `0` is success and resets the consecutive-failure count;
- every nonzero Wire transaction status counts as one failure;
- failures 1 through 9 return `I2C_RECOVERY_NONE`;
- failure 10 returns `I2C_RECOVERY_RECLOCK` and resets the count, so the next failure starts a new window.

The protected `main.cpp` performs the documented recovery action by switching the bus to 1 MHz and back to 400 kHz. Do not change `main.cpp`, `i2c_recovery.h`, or `platformio.ini`.

Submit the completed C file in place. It must satisfy the protected API and build for the ESP32-S2 PlatformIO target.
