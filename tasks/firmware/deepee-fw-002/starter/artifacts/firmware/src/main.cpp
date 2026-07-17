#include <Arduino.h>

extern "C" {
#include "sht3x_decode.h"
}

void setup() {
    const uint8_t frame[6] = {0U};
    SHT3xMeasurement measurement{};
    (void)sht3x_decode_measurement(frame, &measurement);
}

void loop() {}
