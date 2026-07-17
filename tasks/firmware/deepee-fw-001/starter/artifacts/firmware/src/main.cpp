#include <Arduino.h>
#include <Wire.h>

extern "C" {
#include "i2c_recovery.h"
}

namespace {
constexpr int kSdaPin = 8;
constexpr int kSclPin = 9;
constexpr uint8_t kMuxAddress = 0x71;
constexpr uint8_t kOptionalDeviceAddress = 0x60;
constexpr uint32_t kProbePeriodMs = 1000U;

I2CRecoveryState recovery_state;
uint32_t next_probe_ms;

void select_mux_channel_zero() {
    Wire.beginTransmission(kMuxAddress);
    Wire.write(0x01);
    (void)Wire.endTransmission();
}

uint8_t probe_optional_device() {
    Wire.beginTransmission(kOptionalDeviceAddress);
    return Wire.endTransmission();
}

void recover_bus_clock() {
    Wire.setClock(I2C_RECOVERY_HZ);
    delayMicroseconds(10U);
    Wire.setClock(I2C_NOMINAL_HZ);
}
}  // namespace

void setup() {
    Serial.begin(115200);
    Wire.begin(kSdaPin, kSclPin, I2C_NOMINAL_HZ);
    i2c_recovery_init(&recovery_state);
    next_probe_ms = millis();
}

void loop() {
    const uint32_t now_ms = millis();
    if (static_cast<int32_t>(now_ms - next_probe_ms) < 0) {
        return;
    }
    next_probe_ms += kProbePeriodMs;
    select_mux_channel_zero();
    const uint8_t status = probe_optional_device();
    if (i2c_recovery_record(&recovery_state, status) == I2C_RECOVERY_RECLOCK) {
        recover_bus_clock();
    }
}
