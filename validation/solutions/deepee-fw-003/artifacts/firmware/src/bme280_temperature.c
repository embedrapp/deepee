#include "bme280_temperature.h"

bool bme280_compensate_temperature(
    uint32_t adc_temperature,
    const BME280TemperatureCalibration *calibration,
    int32_t *temperature_centicelsius,
    int32_t *t_fine
) {
    if (adc_temperature > 0xFFFFFU || calibration == 0 || temperature_centicelsius == 0 || t_fine == 0) {
        return false;
    }
    const int32_t var1 = ((((int32_t)(adc_temperature >> 3U) -
                            ((int32_t)calibration->dig_t1 << 1U))) *
                          (int32_t)calibration->dig_t2) >> 11U;
    const int32_t delta = (int32_t)(adc_temperature >> 4U) - (int32_t)calibration->dig_t1;
    const int32_t var2 = (((delta * delta) >> 12U) * (int32_t)calibration->dig_t3) >> 14U;
    const int32_t fine = var1 + var2;
    const int32_t temperature = (fine * 5 + 128) >> 8U;
    *t_fine = fine;
    *temperature_centicelsius = temperature;
    return true;
}
