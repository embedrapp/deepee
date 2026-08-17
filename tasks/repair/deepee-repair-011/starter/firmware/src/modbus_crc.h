#ifndef DEEPEE_MODBUS_CRC_H
#define DEEPEE_MODBUS_CRC_H
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
uint16_t modbus_crc16(const uint8_t *data,size_t length);
bool modbus_rtu_frame_valid(const uint8_t *frame,size_t length);
#endif
