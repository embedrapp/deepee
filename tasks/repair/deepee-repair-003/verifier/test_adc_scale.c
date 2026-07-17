#include "adc_scale.h"

#include <limits.h>
#include <stdio.h>
#include <stdlib.h>

static void require_true(int value, const char *message) {
    if (!value) {
        fprintf(stderr, "%s\n", message);
        exit(1);
    }
}

int main(void) {
    int32_t output = 1234567;

    require_true(adc_scale_to_microvolts(2048, 3300000, 12U, &output), "12-bit conversion failed");
    require_true(output == 1650000, "12-bit conversion is incorrect");
    require_true(adc_scale_to_microvolts(-2048, 3300000, 12U, &output), "negative conversion failed");
    require_true(output == -1650000, "negative conversion is incorrect");
    require_true(adc_scale_to_microvolts(1, 3, 1U, &output), "truncating conversion failed");
    require_true(output == 1, "conversion did not truncate toward zero");
    require_true(adc_scale_to_microvolts(-1, 3, 1U, &output), "negative truncating conversion failed");
    require_true(output == -1, "negative conversion did not truncate toward zero");

    output = 99;
    require_true(!adc_scale_to_microvolts(INT32_MAX, INT32_MAX, 1U, &output), "overflow was accepted");
    require_true(output == 99, "failed conversion modified output");
    require_true(!adc_scale_to_microvolts(1, 3300000, 0U, &output), "zero resolution was accepted");
    require_true(!adc_scale_to_microvolts(1, 3300000, 31U, &output), "oversized resolution was accepted");
    require_true(!adc_scale_to_microvolts(1, 0, 12U, &output), "zero reference was accepted");
    require_true(!adc_scale_to_microvolts(1, 3300000, 12U, 0), "null output was accepted");
    return 0;
}
