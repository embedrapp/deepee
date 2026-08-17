#include "time32.h"
#include <limits.h>
bool time32_deadline_reached(uint32_t n,uint32_t d){return (int32_t)(n-d)>=0;}
uint32_t time32_elapsed(uint32_t n,uint32_t t){return n-t;}
bool time32_schedule_after(uint32_t n,uint32_t delay,uint32_t*d){if(!d||delay>INT32_MAX)return false;*d=n+delay;return true;}
