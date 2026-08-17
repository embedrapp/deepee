#ifndef DEEPEE_INA219_DECODE_H
#define DEEPEE_INA219_DECODE_H
#include <stdbool.h>
#include <stdint.h>
typedef struct {
    int32_t shunt_microvolts;
    uint32_t bus_microvolts;
    bool conversion_ready;
    bool math_overflow;
} INA219Reading;
bool ina219_decode(uint16_t shunt_register, uint16_t bus_register, INA219Reading *out);
#endif
