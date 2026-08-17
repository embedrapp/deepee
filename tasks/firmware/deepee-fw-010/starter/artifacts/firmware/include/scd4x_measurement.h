#ifndef DEEPEE_SCD4X_MEASUREMENT_H
#define DEEPEE_SCD4X_MEASUREMENT_H
#include <stdbool.h>
#include <stdint.h>
typedef struct { uint16_t co2_ppm; int32_t temperature_millic; uint32_t humidity_millipercent; } SCD4xMeasurement;
bool scd4x_decode_measurement(const uint8_t response[9], SCD4xMeasurement *out);
#endif
