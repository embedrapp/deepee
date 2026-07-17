#include "adc_scale.h"

#include <limits.h>

bool adc_scale_to_microvolts(
    int32_t raw,
    int32_t reference_uv,
    uint8_t resolution,
    int32_t *output_uv
) {
    if (output_uv == 0 || reference_uv <= 0 || resolution == 0U || resolution > 30U) {
        return false;
    }
    const int64_t numerator = (int64_t)raw * (int64_t)reference_uv;
    const int64_t result = numerator / ((int64_t)1 << resolution);
    if (result < INT32_MIN || result > INT32_MAX) {
        return false;
    }
    *output_uv = (int32_t)result;
    return true;
}
