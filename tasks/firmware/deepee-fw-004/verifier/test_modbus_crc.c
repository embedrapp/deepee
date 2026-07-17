#include "modbus_crc.h"

#include <stdio.h>
#include <stdlib.h>

static void require_true(int value, const char *message) {
    if (!value) {
        fprintf(stderr, "%s\n", message);
        exit(1);
    }
}

int main(void) {
    const uint8_t payload[] = {0x01U, 0x03U, 0x00U, 0x00U, 0x00U, 0x0AU};
    uint8_t frame[8] = {0x01U, 0x03U, 0x00U, 0x00U, 0x00U, 0x0AU, 0U, 0U};

    require_true(modbus_crc16(payload, sizeof(payload)) == 0xCDC5U, "canonical CRC vector failed");
    require_true(modbus_crc16(payload, 0U) == 0xFFFFU, "empty CRC initial value is wrong");
    require_true(modbus_rtu_append_crc(frame, 6U, sizeof(frame)) == sizeof(frame), "CRC append failed");
    require_true(frame[6] == 0xC5U && frame[7] == 0xCDU, "CRC bytes have wrong value or order");
    require_true(modbus_rtu_frame_valid(frame, sizeof(frame)), "valid RTU frame was rejected");

    frame[3] ^= 0x01U;
    require_true(!modbus_rtu_frame_valid(frame, sizeof(frame)), "corrupt payload was accepted");
    frame[3] ^= 0x01U;
    frame[7] ^= 0x01U;
    require_true(!modbus_rtu_frame_valid(frame, sizeof(frame)), "corrupt CRC was accepted");
    require_true(!modbus_rtu_frame_valid(frame, 2U), "undersized frame was accepted");
    require_true(!modbus_rtu_frame_valid(0, sizeof(frame)), "null frame was accepted");
    require_true(modbus_rtu_append_crc(frame, 7U, sizeof(frame)) == 0U, "insufficient capacity was accepted");
    require_true(modbus_rtu_append_crc(0, 0U, 2U) == 0U, "null append buffer was accepted");
    return 0;
}
