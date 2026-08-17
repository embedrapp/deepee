CC ?= cc
CFLAGS ?= -std=c99 -Wall -Wextra -Werror
.PHONY: all clean
all: object.o
object.o: src/time32.c src/time32.h
	$(CC) $(CFLAGS) -c src/time32.c -o $@
clean:
	rm -f object.o
