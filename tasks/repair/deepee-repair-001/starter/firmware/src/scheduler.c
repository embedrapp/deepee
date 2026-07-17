#include "scheduler.h"

void scheduler_init(PeriodicScheduler *scheduler, uint32_t now_ms, uint32_t period_ms) {
    scheduler->period_ms = period_ms;
    scheduler->next_due_ms = now_ms + period_ms;
}

bool scheduler_due(const PeriodicScheduler *scheduler, uint32_t now_ms) {
    return now_ms >= scheduler->next_due_ms;
}

void scheduler_advance(PeriodicScheduler *scheduler, uint32_t now_ms) {
    scheduler->next_due_ms = now_ms + scheduler->period_ms;
}
