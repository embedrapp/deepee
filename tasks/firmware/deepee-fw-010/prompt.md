# Decode an SCD4x measurement response

Complete `src/scd4x_measurement.c`. A measurement response contains
three big-endian 16-bit words—CO2, temperature, and relative humidity—
with a CRC byte after each word. Validate every CRC using polynomial
0x31 and initial value 0xFF.

Return CO2 in ppm, temperature in millidegrees Celsius using
`-45 + 175 * raw / 65535`, and humidity in milli-percent RH using
`100 * raw / 65535`. Use integer arithmetic and reject null pointers or
any CRC failure without modifying the output.
