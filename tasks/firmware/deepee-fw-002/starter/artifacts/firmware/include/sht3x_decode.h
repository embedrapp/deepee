#ifndef DEEPEE_SHT3X_DECODE_H
#define DEEPEE_SHT3X_DECODE_H

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

typedef struct {
    int32_t temperature_millicelsius;
    uint32_t humidity_millipercent;
} SHT3xMeasurement;

uint8_t sht3x_crc8(const uint8_t *data, size_t length);
bool sht3x_decode_measurement(const uint8_t frame[6], SHT3xMeasurement *measurement);

#endif
