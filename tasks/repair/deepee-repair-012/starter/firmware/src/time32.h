#ifndef DEEPEE_TIME32_H
#define DEEPEE_TIME32_H
#include <stdbool.h>
#include <stdint.h>
bool time32_deadline_reached(uint32_t now,uint32_t deadline);
uint32_t time32_elapsed(uint32_t now,uint32_t then);
bool time32_schedule_after(uint32_t now,uint32_t delay,uint32_t *deadline);
#endif
