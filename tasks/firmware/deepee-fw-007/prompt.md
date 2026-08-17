# Implement BMP280 temperature compensation

Complete `src/bmp280_temperature.c` using Bosch's integer compensation
algorithm. The function receives the uncompensated 20-bit temperature
reading and calibration coefficients `dig_T1`, `dig_T2`, and `dig_T3`.
Return temperature in hundredths of a degree Celsius and also return
`t_fine`, because the pressure path consumes it later.

Match the datasheet's signed arithmetic and shift order exactly. Reject
null output pointers and raw ADC values outside 0..0xFFFFF. Do not change
the protected integration files.
