#ifndef DEEPEE_MAX31855_DECODE_H
#define DEEPEE_MAX31855_DECODE_H
#include <stdbool.h>
#include <stdint.h>
typedef struct { int32_t thermocouple_microc; int32_t internal_microc; bool fault; bool short_vcc; bool short_gnd; bool open_circuit; } MAX31855Reading;
bool max31855_decode(uint32_t frame, MAX31855Reading *out);
#endif
