CC ?= cc
CFLAGS ?= -std=c99 -Wall -Wextra -Werror

.PHONY: all clean

all: ring_buffer.o

ring_buffer.o: src/ring_buffer.c src/ring_buffer.h
	$(CC) $(CFLAGS) -c src/ring_buffer.c -o $@

clean:
	rm -f ring_buffer.o
