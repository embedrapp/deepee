#ifndef DEEPEE_HTTP_CHUNK_SIZE_H
#define DEEPEE_HTTP_CHUNK_SIZE_H
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
bool http_parse_chunk_size(const char *line,size_t length,uint64_t *size,size_t *extension_offset);
#endif
