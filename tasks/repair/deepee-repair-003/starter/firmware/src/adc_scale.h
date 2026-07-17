#ifndef DEEPEE_ADC_SCALE_H
#define DEEPEE_ADC_SCALE_H

#include <stdbool.h>
#include <stdint.h>

bool adc_scale_to_microvolts(
    int32_t raw,
    int32_t reference_uv,
    uint8_t resolution,
    int32_t *output_uv
);

#endif
