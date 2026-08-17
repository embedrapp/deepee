CC ?= cc
CFLAGS ?= -std=c99 -Wall -Wextra -Werror
.PHONY: all clean
all: object.o
object.o: src/base64_decode.c src/base64_decode.h
	$(CC) $(CFLAGS) -c src/base64_decode.c -o $@
clean:
	rm -f object.o
