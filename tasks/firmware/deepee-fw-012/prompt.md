# Decode MAX31855 thermocouple frames

Complete `src/max31855_decode.c`. Decode the signed 14-bit
thermocouple field in bits 31:18 and the signed 12-bit internal
temperature field in bits 15:4. Return both in microdegrees Celsius;
their LSBs are 0.25 °C and 0.0625 °C respectively.

Preserve the general fault flag in bit 16 and the short-to-VCC,
short-to-ground, and open-circuit flags in bits 2:0. Reject a null
destination without writing anything.
