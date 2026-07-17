#include "sht3x_decode.h"

uint8_t sht3x_crc8(const uint8_t *data, size_t length) {
    (void)data;
    (void)length;
    return 0U;
}

bool sht3x_decode_measurement(const uint8_t frame[6], SHT3xMeasurement *measurement) {
    (void)frame;
    (void)measurement;
    return false;
}
