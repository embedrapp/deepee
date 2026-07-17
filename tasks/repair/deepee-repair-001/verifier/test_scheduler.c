#include "scheduler.h"

#include <stdio.h>
#include <stdlib.h>

static void require_true(bool value, const char *message) {
    if (!value) {
        fprintf(stderr, "%s\n", message);
        exit(1);
    }
}

int main(void) {
    PeriodicScheduler scheduler;

    scheduler_init(&scheduler, 100U, 1000U);
    require_true(!scheduler_due(&scheduler, 1099U), "ordinary deadline fired early");
    require_true(scheduler_due(&scheduler, 1100U), "ordinary deadline did not fire");
    scheduler_advance(&scheduler, 3650U);
    require_true(scheduler.next_due_ms == 4100U, "late execution changed scheduler cadence");
    require_true(!scheduler_due(&scheduler, 4099U), "advanced deadline fired early");
    require_true(scheduler_due(&scheduler, 4100U), "advanced deadline did not fire");

    scheduler_init(&scheduler, UINT32_MAX - 20U, 50U);
    require_true(scheduler.next_due_ms == 29U, "deadline did not wrap naturally");
    require_true(!scheduler_due(&scheduler, UINT32_MAX - 1U), "rollover deadline fired before wrap");
    require_true(!scheduler_due(&scheduler, 28U), "rollover deadline fired early");
    require_true(scheduler_due(&scheduler, 29U), "rollover deadline did not fire");
    scheduler_advance(&scheduler, 140U);
    require_true(scheduler.next_due_ms == 179U, "missed rollover periods were not caught up");

    scheduler_init(&scheduler, 0U, 1U);
    scheduler_advance(&scheduler, 1000000U);
    require_true(scheduler.next_due_ms == 1000001U, "large missed-period catch-up failed");
    return 0;
}
