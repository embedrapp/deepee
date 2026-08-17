#ifndef DEEPEE_BASE64_DECODE_H
#define DEEPEE_BASE64_DECODE_H
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
bool base64_decode(const char *input,size_t length,uint8_t *output,size_t capacity,size_t *output_length);
#endif
