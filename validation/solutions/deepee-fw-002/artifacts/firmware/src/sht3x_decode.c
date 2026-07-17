#include "sht3x_decode.h"

uint8_t sht3x_crc8(const uint8_t *data, size_t length) {
    uint8_t crc = 0xFFU;
    for (size_t index = 0U; index < length; ++index) {
        crc ^= data[index];
        for (uint8_t bit = 0U; bit < 8U; ++bit) {
            crc = (crc & 0x80U) != 0U ? (uint8_t)((crc << 1U) ^ 0x31U) : (uint8_t)(crc << 1U);
        }
    }
    return crc;
}

bool sht3x_decode_measurement(const uint8_t frame[6], SHT3xMeasurement *measurement) {
    if (frame == 0 || measurement == 0 ||
        sht3x_crc8(frame, 2U) != frame[2] || sht3x_crc8(frame + 3U, 2U) != frame[5]) {
        return false;
    }
    const uint16_t raw_temperature = (uint16_t)(((uint16_t)frame[0] << 8U) | frame[1]);
    const uint16_t raw_humidity = (uint16_t)(((uint16_t)frame[3] << 8U) | frame[4]);
    measurement->temperature_millicelsius =
        -45000 + (int32_t)(((int64_t)175000 * raw_temperature + 32767) / 65535);
    measurement->humidity_millipercent =
        (uint32_t)(((uint64_t)100000 * raw_humidity + 32767U) / 65535U);
    return true;
}
