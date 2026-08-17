#ifndef DEEPEE_SLIP_DECODE_H
#define DEEPEE_SLIP_DECODE_H
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
bool slip_decode(const uint8_t *frame,size_t length,uint8_t *output,size_t capacity,size_t *output_length);
#endif
