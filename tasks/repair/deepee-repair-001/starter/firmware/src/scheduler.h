#ifndef DEEPEE_SCHEDULER_H
#define DEEPEE_SCHEDULER_H

#include <stdbool.h>
#include <stdint.h>

typedef struct {
    uint32_t next_due_ms;
    uint32_t period_ms;
} PeriodicScheduler;

void scheduler_init(PeriodicScheduler *scheduler, uint32_t now_ms, uint32_t period_ms);
bool scheduler_due(const PeriodicScheduler *scheduler, uint32_t now_ms);
void scheduler_advance(PeriodicScheduler *scheduler, uint32_t now_ms);

#endif
