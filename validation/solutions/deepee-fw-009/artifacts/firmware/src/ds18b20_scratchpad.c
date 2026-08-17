#include "ds18b20_scratchpad.h"
static uint8_t crc8(const uint8_t *data, unsigned length) {
    uint8_t crc = 0;
    while (length--) {
        uint8_t value = *data++;
        for (unsigned i = 0; i < 8; ++i) {
            uint8_t mix = (uint8_t)((crc ^ value) & 1U);
            crc >>= 1;
            if (mix) crc ^= 0x8CU;
            value >>= 1;
        }
    }
    return crc;
}
bool ds18b20_decode_scratchpad(const uint8_t s[9], int32_t *temperature_microc,
                               uint8_t *resolution_bits) {
    if (!s || !temperature_microc || !resolution_bits || crc8(s, 8) != s[8]) return false;
    uint8_t resolution = (uint8_t)(9U + ((s[4] >> 5) & 3U));
    int16_t raw = (int16_t)((uint16_t)s[0] | ((uint16_t)s[1] << 8));
    unsigned undefined = 12U - resolution;
    raw = (int16_t)(raw & (int16_t)~((1U << undefined) - 1U));
    *temperature_microc = (int32_t)raw * 62500;
    *resolution_bits = resolution;
    return true;
}
