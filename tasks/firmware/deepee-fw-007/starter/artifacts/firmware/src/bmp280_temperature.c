#include "bmp280_temperature.h"
bool bmp280_compensate_temperature(int32_t adc_t, uint16_t dig_t1, int16_t dig_t2,
                                   int16_t dig_t3, int32_t *temperature_centi_c,
                                   int32_t *t_fine) {
    (void)dig_t3;
    if (!temperature_centi_c || !t_fine) return false;
    int32_t var1 = (((adc_t >> 3) - ((int32_t)dig_t1 << 1)) * dig_t2) >> 11;
    *t_fine = var1;
    *temperature_centi_c = (var1 * 5 + 128) >> 8;
    return true;
}
