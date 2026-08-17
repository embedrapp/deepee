#include "bmp280_temperature.h"
bool bmp280_compensate_temperature(int32_t adc_t, uint16_t dig_t1, int16_t dig_t2,
                                   int16_t dig_t3, int32_t *temperature_centi_c,
                                   int32_t *t_fine) {
    if (!temperature_centi_c || !t_fine || adc_t < 0 || adc_t > 0xFFFFF) return false;
    int32_t var1 = ((((adc_t >> 3) - ((int32_t)dig_t1 << 1))) * (int32_t)dig_t2) >> 11;
    int32_t delta = (adc_t >> 4) - (int32_t)dig_t1;
    int32_t var2 = (int32_t)((((int64_t)delta * delta) >> 12) * dig_t3 >> 14);
    int32_t fine = var1 + var2;
    *t_fine = fine;
    *temperature_centi_c = (fine * 5 + 128) >> 8;
    return true;
}
