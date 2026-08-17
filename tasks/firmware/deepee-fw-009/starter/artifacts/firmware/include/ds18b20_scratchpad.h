#ifndef DEEPEE_DS18B20_SCRATCHPAD_H
#define DEEPEE_DS18B20_SCRATCHPAD_H
#include <stdbool.h>
#include <stdint.h>
bool ds18b20_decode_scratchpad(const uint8_t scratchpad[9], int32_t *temperature_microc,
                               uint8_t *resolution_bits);
#endif
