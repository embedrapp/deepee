CC ?= cc
CFLAGS ?= -std=c99 -Wall -Wextra -Werror
.PHONY: all clean
all: object.o
object.o: src/http_chunk_size.c src/http_chunk_size.h
	$(CC) $(CFLAGS) -c src/http_chunk_size.c -o $@
clean:
	rm -f object.o
