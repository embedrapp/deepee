# Implement BME280 integer temperature compensation

Complete `src/bme280_temperature.c` using the protected API and Bosch's integer compensation sequence.

The function receives the 20-bit raw temperature ADC value and the `dig_T1`, `dig_T2`, and `dig_T3` calibration coefficients. It must calculate `t_fine` and return temperature in hundredths of a degree Celsius. For the datasheet vector `dig_T1=27504`, `dig_T2=26435`, `dig_T3=-1000`, and `adc_T=519888`, the outputs are `t_fine=128422` and `temperature=2508` (25.08 °C).

Reject null pointers and raw ADC values above `0xFFFFF`; do not modify outputs on failure. Use fixed-width integer arithmetic and preserve the shift/order semantics of Bosch's documented algorithm.

Do not change `bme280_temperature.h`, `main.cpp`, or `platformio.ini`. Submit the completed C file in place. It must pass native verifier vectors and the ESP32-S2 build.
