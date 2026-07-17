#include "i2c_recovery.h"

#include <stdio.h>
#include <stdlib.h>

static void require_true(int value, const char *message) {
    if (!value) {
        fprintf(stderr, "%s\n", message);
        exit(1);
    }
}

int main(void) {
    I2CRecoveryState state;
    i2c_recovery_init(&state);
    require_true(state.consecutive_failures == 0U, "initial failure count is not zero");

    for (uint8_t failure = 1U; failure < I2C_FAILURE_THRESHOLD; ++failure) {
        require_true(i2c_recovery_record(&state, 2U) == I2C_RECOVERY_NONE, "recovery fired before threshold");
        require_true(state.consecutive_failures == failure, "failure count did not advance");
    }
    require_true(i2c_recovery_record(&state, 2U) == I2C_RECOVERY_RECLOCK, "recovery did not fire at threshold");
    require_true(state.consecutive_failures == 0U, "threshold did not reset failure window");

    require_true(i2c_recovery_record(&state, 4U) == I2C_RECOVERY_NONE, "non-address error triggered early recovery");
    require_true(state.consecutive_failures == 1U, "non-address error was not counted");
    require_true(i2c_recovery_record(&state, 0U) == I2C_RECOVERY_NONE, "success requested recovery");
    require_true(state.consecutive_failures == 0U, "success did not reset failure count");

    for (uint8_t failure = 1U; failure <= I2C_FAILURE_THRESHOLD; ++failure) {
        const I2CRecoveryAction expected = failure == I2C_FAILURE_THRESHOLD
            ? I2C_RECOVERY_RECLOCK
            : I2C_RECOVERY_NONE;
        require_true(i2c_recovery_record(&state, 5U) == expected, "second failure window is incorrect");
    }
    return 0;
}
