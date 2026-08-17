#include "scd4x_measurement.h"
static uint8_t crc_word(const uint8_t *p) {
    uint8_t crc = 0xFF;
    for (unsigned b=0;b<2;b++) { crc ^= p[b]; for (unsigned i=0;i<8;i++) crc = (crc & 0x80U) ? (uint8_t)((crc << 1) ^ 0x31U) : (uint8_t)(crc << 1); }
    return crc;
}
bool scd4x_decode_measurement(const uint8_t r[9], SCD4xMeasurement *out) {
    if (!r || !out || crc_word(r)!=r[2] || crc_word(r+3)!=r[5] || crc_word(r+6)!=r[8]) return false;
    uint16_t co2=(uint16_t)((r[0]<<8)|r[1]);
    uint16_t tr=(uint16_t)((r[3]<<8)|r[4]);
    uint16_t hr=(uint16_t)((r[6]<<8)|r[7]);
    SCD4xMeasurement value = { co2, -45000 + (int32_t)((175000LL*tr)/65535LL), (uint32_t)((100000ULL*hr)/65535ULL) };
    *out=value;
    return true;
}
