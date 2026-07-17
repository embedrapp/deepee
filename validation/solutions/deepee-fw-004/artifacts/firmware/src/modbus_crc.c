#include "modbus_crc.h"

uint16_t modbus_crc16(const uint8_t *data, size_t length) {
    uint16_t crc = 0xFFFFU;
    for (size_t index = 0U; index < length; ++index) {
        crc ^= data[index];
        for (uint8_t bit = 0U; bit < 8U; ++bit) {
            crc = (crc & 1U) != 0U ? (uint16_t)((crc >> 1U) ^ 0xA001U) : (uint16_t)(crc >> 1U);
        }
    }
    return crc;
}

size_t modbus_rtu_append_crc(uint8_t *frame, size_t payload_length, size_t capacity) {
    if (frame == 0 || payload_length > capacity || capacity - payload_length < 2U) {
        return 0U;
    }
    const uint16_t crc = modbus_crc16(frame, payload_length);
    frame[payload_length] = (uint8_t)crc;
    frame[payload_length + 1U] = (uint8_t)(crc >> 8U);
    return payload_length + 2U;
}

bool modbus_rtu_frame_valid(const uint8_t *frame, size_t frame_length) {
    if (frame == 0 || frame_length < 3U) {
        return false;
    }
    const size_t payload_length = frame_length - 2U;
    const uint16_t expected = modbus_crc16(frame, payload_length);
    const uint16_t actual = (uint16_t)(frame[payload_length] |
                                       ((uint16_t)frame[payload_length + 1U] << 8U));
    return expected == actual;
}
