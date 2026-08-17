CC ?= cc
CFLAGS ?= -std=c99 -Wall -Wextra -Werror
.PHONY: all clean
all: object.o
object.o: src/utf8_decode.c src/utf8_decode.h
	$(CC) $(CFLAGS) -c src/utf8_decode.c -o $@
clean:
	rm -f object.o
