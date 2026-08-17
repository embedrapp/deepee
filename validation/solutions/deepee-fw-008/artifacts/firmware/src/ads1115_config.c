#include "ads1115_config.h"
bool ads1115_build_config(uint8_t mux, uint8_t pga, uint8_t data_rate,
                          bool continuous, bool comparator_enable, uint16_t *config) {
    if (!config || mux > 7U || pga > 5U || data_rate > 7U) return false;
    uint16_t value = 0x8000U;
    value |= (uint16_t)mux << 12;
    value |= (uint16_t)pga << 9;
    if (!continuous) value |= 0x0100U;
    value |= (uint16_t)data_rate << 5;
    value |= comparator_enable ? 0U : 3U;
    *config = value;
    return true;
}
