#ifndef DEEPEE_BME280_TEMPERATURE_H
#define DEEPEE_BME280_TEMPERATURE_H

#include <stdbool.h>
#include <stdint.h>

typedef struct {
    uint16_t dig_t1;
    int16_t dig_t2;
    int16_t dig_t3;
} BME280TemperatureCalibration;

bool bme280_compensate_temperature(
    uint32_t adc_temperature,
    const BME280TemperatureCalibration *calibration,
    int32_t *temperature_centicelsius,
    int32_t *t_fine
);

#endif
