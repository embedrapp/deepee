#ifndef DEEPEE_BMP280_TEMPERATURE_H
#define DEEPEE_BMP280_TEMPERATURE_H
#include <stdbool.h>
#include <stdint.h>
bool bmp280_compensate_temperature(int32_t adc_t, uint16_t dig_t1, int16_t dig_t2,
                                   int16_t dig_t3, int32_t *temperature_centi_c,
                                   int32_t *t_fine);
#endif
