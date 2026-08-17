#include "bmp280_temperature.h"
#include <stdio.h>
#include <stdlib.h>
static void req(int ok, const char *m) { if (!ok) { fprintf(stderr, "%s\n", m); exit(1); } }
int main(void) {
    int32_t t = 0, fine = 0;
    req(bmp280_compensate_temperature(519888, 27504, 26435, -1000, &t, &fine), "datasheet vector rejected");
    req(t == 2508 && fine == 128422, "datasheet vector wrong");
    req(bmp280_compensate_temperature(0, 27504, 26435, -1000, &t, &fine), "zero raw rejected");
    req(t == -14088, "cold-range signed arithmetic wrong");
    req(!bmp280_compensate_temperature(-1, 1, 1, 1, &t, &fine), "negative raw accepted");
    req(!bmp280_compensate_temperature(0, 1, 1, 1, 0, &fine), "null output accepted");
    return 0;
}
