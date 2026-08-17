#include "ina219_decode.h"
#include <stdio.h>
#include <stdlib.h>
static void req(int ok, const char *m) { if (!ok) { fprintf(stderr, "%s\n", m); exit(1); } }
int main(void) {
    INA219Reading r;
    req(ina219_decode(0x0064, (uint16_t)((3000U << 3) | 2U), &r), "nominal decode failed");
    req(r.shunt_microvolts == 1000 && r.bus_microvolts == 12000000U, "voltage decode wrong");
    req(r.conversion_ready && !r.math_overflow, "status decode wrong");
    req(ina219_decode(0xFF9C, 1U, &r), "negative decode failed");
    req(r.shunt_microvolts == -1000 && r.math_overflow && !r.conversion_ready, "signed/status decode wrong");
    req(!ina219_decode(0, 0, 0), "null output accepted");
    return 0;
}
