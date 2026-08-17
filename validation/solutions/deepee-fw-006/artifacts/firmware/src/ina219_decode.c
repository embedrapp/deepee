#include "ina219_decode.h"
bool ina219_decode(uint16_t shunt_register, uint16_t bus_register, INA219Reading *out) {
    if (out == 0) return false;
    out->shunt_microvolts = (int32_t)(int16_t)shunt_register * 10;
    out->bus_microvolts = (uint32_t)(bus_register >> 3) * 4000U;
    out->conversion_ready = (bus_register & 2U) != 0U;
    out->math_overflow = (bus_register & 1U) != 0U;
    return true;
}
