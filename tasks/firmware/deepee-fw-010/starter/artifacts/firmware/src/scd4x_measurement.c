#include "scd4x_measurement.h"
bool scd4x_decode_measurement(const uint8_t r[9], SCD4xMeasurement *out) {
    if (!r || !out) return false;
    out->co2_ppm = (uint16_t)((r[0] << 8) | r[1]);
    out->temperature_millic = -45000 + (175000 * (int32_t)((r[3] << 8) | r[4])) / 65536;
    out->humidity_millipercent = (100000U * (uint32_t)((r[6] << 8) | r[7])) / 65536U;
    return true;
}
