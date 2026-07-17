# Task provenance

Adapted from Zephyr's documented byte ring-buffer semantics: normal put/get operations preserve stream order across the backing-buffer boundary, transfer no more than available data or space, and leave concurrency control to the caller when the access pattern requires it.

- Zephyr ring-buffer documentation: https://docs.zephyrproject.org/latest/kernel/data_structures/ring_buffers.html
- Zephyr ring-buffer API: https://docs.zephyrproject.org/latest/doxygen/html/group__ring__buffer__apis.html

The compact API and faulty starter are original benchmark material. No Zephyr source code is copied.
