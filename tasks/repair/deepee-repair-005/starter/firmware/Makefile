CC ?= cc
CFLAGS ?= -std=c99 -Wall -Wextra -Werror
.PHONY: all clean
all: object.o
object.o: src/mqtt_remaining_length.c src/mqtt_remaining_length.h
	$(CC) $(CFLAGS) -c src/mqtt_remaining_length.c -o $@
clean:
	rm -f object.o
