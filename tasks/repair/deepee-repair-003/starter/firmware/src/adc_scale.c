#include "adc_scale.h"

bool adc_scale_to_microvolts(
    int32_t raw,
    int32_t reference_uv,
    uint8_t resolution,
    int32_t *output_uv
) {
    if (output_uv == 0 || reference_uv <= 0 || resolution == 0U || resolution > 30U) {
        return false;
    }
    *output_uv = (raw * reference_uv) / (1 << resolution);
    return true;
}
