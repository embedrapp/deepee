#include "pca9685_timing.h"

bool pca9685_compute_prescale(uint32_t oscillator_hz, uint32_t pwm_hz, uint8_t *prescale) {
  if (!prescale || !oscillator_hz || !pwm_hz) {
    return false;
  }
  uint64_t denominator = 4096ULL * pwm_hz;
  uint64_t rounded_ratio = (oscillator_hz + denominator / 2) / denominator;
  if (rounded_ratio == 0) {
    return false;
  }
  uint64_t value = rounded_ratio - 1;
  if (value < 3 || value > 255) {
    return false;
  }
  *prescale = (uint8_t)value;
  return true;
}

bool pca9685_encode_channel(
    uint16_t on,
    uint16_t off,
    bool full_on,
    bool full_off,
    uint8_t bytes[4]
) {
  if (!bytes || on > 4095 || off > 4095 || (full_on && full_off)) {
    return false;
  }
  const uint8_t encoded[4] = {
      (uint8_t)on,
      (uint8_t)((on >> 8) | (full_on ? 0x10 : 0)),
      (uint8_t)off,
      (uint8_t)((off >> 8) | (full_off ? 0x10 : 0)),
  };
  for (int index = 0; index < 4; ++index) {
    bytes[index] = encoded[index];
  }
  return true;
}
