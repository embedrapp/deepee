#include "i2c_recovery.h"

void i2c_recovery_init(I2CRecoveryState *state) {
    state->consecutive_failures = 0U;
}

I2CRecoveryAction i2c_recovery_record(I2CRecoveryState *state, uint8_t wire_status) {
    (void)state;
    (void)wire_status;
    return I2C_RECOVERY_NONE;
}
