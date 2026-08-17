CC ?= cc
CFLAGS ?= -std=c99 -Wall -Wextra -Werror
.PHONY: all clean
all: object.o
object.o: src/cbor_uint.c src/cbor_uint.h
	$(CC) $(CFLAGS) -c src/cbor_uint.c -o $@
clean:
	rm -f object.o
