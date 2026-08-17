#ifndef DEEPEE_PCA9685_TIMING_H
#define DEEPEE_PCA9685_TIMING_H
#include <stdbool.h>
#include <stdint.h>
bool pca9685_compute_prescale(uint32_t oscillator_hz, uint32_t pwm_hz, uint8_t *prescale);
bool pca9685_encode_channel(uint16_t on, uint16_t off, bool full_on, bool full_off, uint8_t bytes[4]);
#endif
