#ifndef DEEPEE_RING_BUFFER_H
#define DEEPEE_RING_BUFFER_H

#include <stddef.h>
#include <stdint.h>

#define BYTE_RING_CAPACITY 8U

typedef struct {
    uint8_t storage[BYTE_RING_CAPACITY];
    size_t read_index;
    size_t write_index;
    size_t count;
} ByteRing;

void byte_ring_init(ByteRing *ring);
size_t byte_ring_write(ByteRing *ring, const uint8_t *source, size_t length);
size_t byte_ring_read(ByteRing *ring, uint8_t *destination, size_t length);
size_t byte_ring_size(const ByteRing *ring);
size_t byte_ring_space(const ByteRing *ring);

#endif
