#include "ads1115_config.h"
bool ads1115_build_config(uint8_t mux, uint8_t pga, uint8_t data_rate,
                          bool continuous, bool comparator_enable, uint16_t *config) {
    if (!config) return false;
    *config = (uint16_t)(0x8000U | ((uint16_t)mux << 11) | ((uint16_t)pga << 8) |
                         ((uint16_t)data_rate << 4) | (continuous ? 0U : 0x0100U) |
                         (comparator_enable ? 0U : 3U));
    return true;
}
