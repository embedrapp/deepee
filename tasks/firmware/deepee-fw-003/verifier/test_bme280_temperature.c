#include "bme280_temperature.h"

#include <stdio.h>
#include <stdlib.h>

static void require_true(int value, const char *message) {
    if (!value) {
        fprintf(stderr, "%s\n", message);
        exit(1);
    }
}

static void reference_compensate(
    uint32_t adc,
    const BME280TemperatureCalibration *calibration,
    int32_t *temperature,
    int32_t *fine
) {
    const int32_t var1 = ((((int32_t)(adc >> 3U) - ((int32_t)calibration->dig_t1 << 1U))) *
                          (int32_t)calibration->dig_t2) >> 11U;
    const int32_t delta = (int32_t)(adc >> 4U) - (int32_t)calibration->dig_t1;
    const int32_t var2 = (((delta * delta) >> 12U) * (int32_t)calibration->dig_t3) >> 14U;
    *fine = var1 + var2;
    *temperature = (*fine * 5 + 128) >> 8U;
}

static void check_vector(uint32_t adc, BME280TemperatureCalibration calibration) {
    int32_t expected_temperature;
    int32_t expected_fine;
    int32_t temperature = 0;
    int32_t fine = 0;
    reference_compensate(adc, &calibration, &expected_temperature, &expected_fine);
    require_true(bme280_compensate_temperature(adc, &calibration, &temperature, &fine),
                 "valid compensation vector was rejected");
    require_true(temperature == expected_temperature, "compensated temperature is wrong");
    require_true(fine == expected_fine, "t_fine is wrong");
}

int main(void) {
    const BME280TemperatureCalibration documented = {27504U, 26435, -1000};
    int32_t temperature = 77;
    int32_t fine = 88;

    require_true(bme280_compensate_temperature(519888U, &documented, &temperature, &fine),
                 "documented vector was rejected");
    require_true(temperature == 2508, "documented temperature vector failed");
    require_true(fine == 128422, "documented t_fine vector failed");
    check_vector(0U, documented);
    check_vector(0xFFFFFU, documented);
    check_vector(400000U, (BME280TemperatureCalibration){30000U, -12000, 2500});

    temperature = 77;
    fine = 88;
    require_true(!bme280_compensate_temperature(0x100000U, &documented, &temperature, &fine),
                 "out-of-range ADC value was accepted");
    require_true(temperature == 77 && fine == 88, "failed call modified outputs");
    require_true(!bme280_compensate_temperature(1U, 0, &temperature, &fine), "null calibration accepted");
    require_true(!bme280_compensate_temperature(1U, &documented, 0, &fine), "null temperature accepted");
    require_true(!bme280_compensate_temperature(1U, &documented, &temperature, 0), "null t_fine accepted");
    return 0;
}
