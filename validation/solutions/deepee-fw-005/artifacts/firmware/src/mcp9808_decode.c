#include "mcp9808_decode.h"

bool mcp9808_decode_ambient(uint16_t register_value, MCP9808Reading *reading) {
    if (reading == 0) {
        return false;
    }
    int32_t units = (int32_t)(register_value & 0x0FFFU);
    if ((register_value & 0x1000U) != 0U) {
        units -= 4096;
    }
    reading->temperature_microcelsius = units * 62500;
    reading->critical_alert = (register_value & 0x8000U) != 0U;
    reading->upper_alert = (register_value & 0x4000U) != 0U;
    reading->lower_alert = (register_value & 0x2000U) != 0U;
    return true;
}
