CC ?= cc
CFLAGS ?= -std=c99 -Wall -Wextra -Werror
.PHONY: all clean
all: object.o
object.o: src/modbus_crc.c src/modbus_crc.h
	$(CC) $(CFLAGS) -c src/modbus_crc.c -o $@
clean:
	rm -f object.o
