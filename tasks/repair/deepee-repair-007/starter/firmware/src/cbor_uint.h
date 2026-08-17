#ifndef DEEPEE_CBOR_UINT_H
#define DEEPEE_CBOR_UINT_H
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
bool cbor_decode_uint(const uint8_t *data,size_t length,uint64_t *value,size_t *consumed);
#endif
