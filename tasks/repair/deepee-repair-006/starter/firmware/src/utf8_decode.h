#ifndef DEEPEE_UTF8_DECODE_H
#define DEEPEE_UTF8_DECODE_H
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
bool utf8_decode_one(const uint8_t *data,size_t length,uint32_t *scalar,size_t *consumed);
#endif
