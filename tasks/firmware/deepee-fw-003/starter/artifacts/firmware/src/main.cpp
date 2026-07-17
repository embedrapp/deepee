#include <Arduino.h>

extern "C" {
#include "bme280_temperature.h"
}

void setup() {
    const BME280TemperatureCalibration calibration{27504U, 26435, -1000};
    int32_t temperature = 0;
    int32_t fine = 0;
    (void)bme280_compensate_temperature(519888U, &calibration, &temperature, &fine);
}

void loop() {}
