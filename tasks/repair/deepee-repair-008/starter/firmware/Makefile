CC ?= cc
CFLAGS ?= -std=c99 -Wall -Wextra -Werror
.PHONY: all clean
all: object.o
object.o: src/ppp_fcs.c src/ppp_fcs.h
	$(CC) $(CFLAGS) -c src/ppp_fcs.c -o $@
clean:
	rm -f object.o
