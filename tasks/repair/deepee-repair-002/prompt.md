# Repair the wrapped byte ring buffer

The supplied fixed-capacity byte FIFO loses data when a write or read crosses the end of its backing array. Repair `firmware/src/ring_buffer.c` using the protected API.

Required behavior:

- preserve FIFO order across any number of index wraparounds;
- write at most the currently available space and return the number written;
- read at most the currently stored byte count and return the number read;
- keep `count`, `read_index`, and `write_index` consistent after partial operations;
- zero-length operations return zero without changing state.

The integration uses one producer and one consumer sequentially; concurrency control is outside this repair. Do not change `ring_buffer.h` or the Makefile.

Submit the repaired `firmware/src/ring_buffer.c` and preserve the documented API behavior.
