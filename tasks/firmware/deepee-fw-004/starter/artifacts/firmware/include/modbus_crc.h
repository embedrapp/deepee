#ifndef DEEPEE_MODBUS_CRC_H
#define DEEPEE_MODBUS_CRC_H

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

uint16_t modbus_crc16(const uint8_t *data, size_t length);
size_t modbus_rtu_append_crc(uint8_t *frame, size_t payload_length, size_t capacity);
bool modbus_rtu_frame_valid(const uint8_t *frame, size_t frame_length);

#endif
