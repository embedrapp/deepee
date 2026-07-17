#ifndef DEEPEE_I2C_RECOVERY_H
#define DEEPEE_I2C_RECOVERY_H

#include <stdint.h>

#define I2C_NOMINAL_HZ 400000U
#define I2C_RECOVERY_HZ 1000000U
#define I2C_FAILURE_THRESHOLD 10U

typedef enum {
    I2C_RECOVERY_NONE = 0,
    I2C_RECOVERY_RECLOCK = 1,
} I2CRecoveryAction;

typedef struct {
    uint8_t consecutive_failures;
} I2CRecoveryState;

void i2c_recovery_init(I2CRecoveryState *state);
I2CRecoveryAction i2c_recovery_record(I2CRecoveryState *state, uint8_t wire_status);

#endif
