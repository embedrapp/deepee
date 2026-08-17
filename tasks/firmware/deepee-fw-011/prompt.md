# Implement PCA9685 timing helpers

Finish `src/pca9685_timing.c`. Compute the PRE_SCALE register from the
oscillator frequency and requested PWM frequency by rounding
`oscillator / (4096 * frequency)` to the nearest integer and subtracting
one. Only register values 3..255 are usable.

Also encode one channel's 12-bit ON and OFF counts into the four LED
register bytes, including the full-on and full-off bits. Counts above
4095 and simultaneous full-on/full-off requests are invalid. Failed
calls must not modify their destination.
