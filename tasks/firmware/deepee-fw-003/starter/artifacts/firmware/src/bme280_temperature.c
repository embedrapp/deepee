#include "bme280_temperature.h"

bool bme280_compensate_temperature(
    uint32_t adc_temperature,
    const BME280TemperatureCalibration *calibration,
    int32_t *temperature_centicelsius,
    int32_t *t_fine
) {
    (void)adc_temperature;
    (void)calibration;
    (void)temperature_centicelsius;
    (void)t_fine;
    return false;
}
