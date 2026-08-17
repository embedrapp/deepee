#ifndef DEEPEE_ADS1115_CONFIG_H
#define DEEPEE_ADS1115_CONFIG_H
#include <stdbool.h>
#include <stdint.h>
bool ads1115_build_config(uint8_t mux, uint8_t pga, uint8_t data_rate,
                          bool continuous, bool comparator_enable, uint16_t *config);
#endif
