#include "time32.h"
bool time32_deadline_reached(uint32_t n,uint32_t d){return n>=d;}
uint32_t time32_elapsed(uint32_t n,uint32_t t){return n-t;}
bool time32_schedule_after(uint32_t n,uint32_t delay,uint32_t*d){if(!d)return false;*d=n+delay;return true;}
