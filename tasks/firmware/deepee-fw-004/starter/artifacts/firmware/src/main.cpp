#include <Arduino.h>

extern "C" {
#include "modbus_crc.h"
}

void setup() {
    uint8_t request[8] = {1U, 3U, 0U, 0U, 0U, 10U};
    (void)modbus_rtu_append_crc(request, 6U, sizeof(request));
}

void loop() {}
