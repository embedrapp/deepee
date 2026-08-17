# Repair the rollover-unsafe scheduler

The starter contains a periodic scheduler with two real embedded failure modes: it compares 32-bit millisecond timestamps directly across rollover, and it drifts when execution is late.

Fix `firmware/src/scheduler.c` so it follows the protected API contract:

- `scheduler_due` must work across `uint32_t` rollover for intervals shorter than `INT32_MAX` milliseconds;
- `scheduler_advance` must advance from the prior deadline by whole periods until the next deadline is strictly in the future, preserving cadence after late execution;
- a zero period is invalid and does not need to be supported.

Do not change `scheduler.h` or the Makefile. Submit the repaired C file in place and preserve the documented API behavior.
