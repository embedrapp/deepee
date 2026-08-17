#include "ads1115_config.h"
#include <stdio.h>
#include <stdlib.h>
static void req(int ok, const char *m) { if (!ok) { fprintf(stderr, "%s\n", m); exit(1); } }
int main(void) {
    uint16_t v = 0;
    req(ads1115_build_config(4, 2, 4, false, false, &v), "single-shot config rejected");
    req(v == 0xC583U, "single-shot config wrong");
    req(ads1115_build_config(7, 5, 7, true, true, &v), "continuous config rejected");
    req(v == 0xFAE0U, "continuous config wrong");
    v = 0x1234;
    req(!ads1115_build_config(0, 6, 0, false, false, &v) && v == 0x1234, "invalid PGA accepted or output changed");
    req(!ads1115_build_config(0, 0, 8, false, false, &v), "invalid rate accepted");
    req(!ads1115_build_config(0, 0, 0, false, false, 0), "null output accepted");
    return 0;
}
