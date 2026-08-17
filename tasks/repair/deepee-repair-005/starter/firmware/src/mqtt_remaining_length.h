#ifndef DEEPEE_MQTT_REMAINING_LENGTH_H
#define DEEPEE_MQTT_REMAINING_LENGTH_H
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
bool mqtt_decode_remaining_length(const uint8_t *data,size_t length,uint32_t *value,size_t *consumed);
#endif
