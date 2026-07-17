#ifndef DEEPEE_MCP9808_DECODE_H
#define DEEPEE_MCP9808_DECODE_H

#include <stdbool.h>
#include <stdint.h>

typedef struct {
    int32_t temperature_microcelsius;
    bool critical_alert;
    bool upper_alert;
    bool lower_alert;
} MCP9808Reading;

bool mcp9808_decode_ambient(uint16_t register_value, MCP9808Reading *reading);

#endif
