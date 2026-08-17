CC ?= cc
CFLAGS ?= -std=c99 -Wall -Wextra -Werror
.PHONY: all clean
all: object.o
object.o: src/slip_decode.c src/slip_decode.h
	$(CC) $(CFLAGS) -c src/slip_decode.c -o $@
clean:
	rm -f object.o
