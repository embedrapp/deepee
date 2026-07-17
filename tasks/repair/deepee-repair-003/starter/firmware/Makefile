CC ?= cc
CFLAGS ?= -std=c99 -Wall -Wextra -Werror

.PHONY: all clean

all: adc_scale.o

adc_scale.o: src/adc_scale.c src/adc_scale.h
	$(CC) $(CFLAGS) -c src/adc_scale.c -o $@

clean:
	rm -f adc_scale.o
