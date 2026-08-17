# Repair wrap-safe tick timing

Repair `firmware/src/time32.c` for a 32-bit millisecond tick counter that
wraps naturally. `time32_deadline_reached` must treat `now` as on or after a
deadline when their signed modular difference is nonnegative. Inputs are
guaranteed to be separated by less than 2^31 ticks. `time32_elapsed` returns
modular elapsed time. `time32_schedule_after` rejects a null destination or
delays of 2^31 ticks and above, otherwise stores `now + delay` modulo 2^32.
