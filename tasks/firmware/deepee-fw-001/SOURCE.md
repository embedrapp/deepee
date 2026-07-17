# Task provenance

Adapted from Espressif Arduino-ESP32 issue #8480. The report uses an ESP32-S2, SDA GPIO 8, SCL GPIO 9, a 400 kHz bus, PCA9547 address `0x71`, and an absent downstream device at `0x60`; repeated failed writes were reported to degrade the bus clock, with a 1 MHz-to-400 kHz re-clocking workaround.

- Source issue: https://github.com/espressif/arduino-esp32/issues/8480
- Adaptation: the hardware-dependent failure is reduced to a deterministic recovery policy with native tests plus a real ESP32-S2 build. No issue code is copied.
