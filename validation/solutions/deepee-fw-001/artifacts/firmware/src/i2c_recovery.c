#include "i2c_recovery.h"

void i2c_recovery_init(I2CRecoveryState *state) {
    state->consecutive_failures = 0U;
}

I2CRecoveryAction i2c_recovery_record(I2CRecoveryState *state, uint8_t wire_status) {
    if (wire_status == 0U) {
        state->consecutive_failures = 0U;
        return I2C_RECOVERY_NONE;
    }
    ++state->consecutive_failures;
    if (state->consecutive_failures >= I2C_FAILURE_THRESHOLD) {
        state->consecutive_failures = 0U;
        return I2C_RECOVERY_RECLOCK;
    }
    return I2C_RECOVERY_NONE;
}
