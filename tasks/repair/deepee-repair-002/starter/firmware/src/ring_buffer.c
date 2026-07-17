#include "ring_buffer.h"

void byte_ring_init(ByteRing *ring) {
    ring->read_index = 0U;
    ring->write_index = 0U;
    ring->count = 0U;
}

size_t byte_ring_write(ByteRing *ring, const uint8_t *source, size_t length) {
    size_t available = BYTE_RING_CAPACITY - ring->write_index;
    size_t transferred = length < available ? length : available;
    for (size_t index = 0U; index < transferred; ++index) {
        ring->storage[ring->write_index++] = source[index];
    }
    ring->count += transferred;
    return transferred;
}

size_t byte_ring_read(ByteRing *ring, uint8_t *destination, size_t length) {
    size_t available = ring->count < length ? ring->count : length;
    for (size_t index = 0U; index < available; ++index) {
        destination[index] = ring->storage[ring->read_index++];
    }
    ring->count -= available;
    return available;
}

size_t byte_ring_size(const ByteRing *ring) {
    return ring->count;
}

size_t byte_ring_space(const ByteRing *ring) {
    return BYTE_RING_CAPACITY - ring->count;
}
