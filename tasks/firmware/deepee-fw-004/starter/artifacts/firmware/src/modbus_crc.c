#include "modbus_crc.h"

uint16_t modbus_crc16(const uint8_t *data, size_t length) {
    (void)data;
    (void)length;
    return 0U;
}

size_t modbus_rtu_append_crc(uint8_t *frame, size_t payload_length, size_t capacity) {
    (void)frame;
    (void)payload_length;
    (void)capacity;
    return 0U;
}

bool modbus_rtu_frame_valid(const uint8_t *frame, size_t frame_length) {
    (void)frame;
    (void)frame_length;
    return false;
}
