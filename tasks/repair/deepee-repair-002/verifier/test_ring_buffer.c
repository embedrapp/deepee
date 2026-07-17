#include "ring_buffer.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static void require_true(int value, const char *message) {
    if (!value) {
        fprintf(stderr, "%s\n", message);
        exit(1);
    }
}

int main(void) {
    ByteRing ring;
    const uint8_t first[] = {1U, 2U, 3U, 4U, 5U, 6U};
    const uint8_t second[] = {7U, 8U, 9U, 10U, 11U, 12U, 13U};
    const uint8_t expected[] = {5U, 6U, 7U, 8U, 9U, 10U, 11U, 12U};
    uint8_t output[BYTE_RING_CAPACITY] = {0U};

    byte_ring_init(&ring);
    require_true(byte_ring_size(&ring) == 0U, "new ring is not empty");
    require_true(byte_ring_space(&ring) == BYTE_RING_CAPACITY, "new ring has wrong capacity");
    require_true(byte_ring_write(&ring, first, 6U) == 6U, "initial write was truncated");
    require_true(byte_ring_read(&ring, output, 4U) == 4U, "initial read was truncated");
    require_true(memcmp(output, first, 4U) == 0, "initial FIFO order is wrong");

    require_true(byte_ring_write(&ring, second, 7U) == 6U, "wrapped write did not stop at capacity");
    require_true(byte_ring_size(&ring) == BYTE_RING_CAPACITY, "full ring has wrong size");
    require_true(byte_ring_space(&ring) == 0U, "full ring reports free space");
    require_true(byte_ring_write(&ring, second, 1U) == 0U, "write succeeded while full");
    require_true(byte_ring_read(&ring, output, sizeof(output)) == sizeof(output), "wrapped read was truncated");
    require_true(memcmp(output, expected, sizeof(expected)) == 0, "wrapped FIFO order is wrong");

    require_true(byte_ring_read(&ring, output, 1U) == 0U, "read succeeded while empty");
    require_true(byte_ring_write(&ring, first, 0U) == 0U, "zero-length write changed state");
    require_true(byte_ring_read(&ring, output, 0U) == 0U, "zero-length read changed state");
    require_true(byte_ring_size(&ring) == 0U && byte_ring_space(&ring) == BYTE_RING_CAPACITY,
                 "ring did not return to empty state");
    return 0;
}
