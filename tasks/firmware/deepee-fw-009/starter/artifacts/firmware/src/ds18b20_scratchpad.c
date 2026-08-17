#include "ds18b20_scratchpad.h"
bool ds18b20_decode_scratchpad(const uint8_t s[9], int32_t *temperature_microc,
                               uint8_t *resolution_bits) {
    if (!s || !temperature_microc || !resolution_bits) return false;
    int16_t raw = (int16_t)((uint16_t)s[0] | ((uint16_t)s[1] << 8));
    *temperature_microc = raw * 62500;
    *resolution_bits = 12;
    return true;
}
