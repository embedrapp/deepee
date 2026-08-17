#include "pca9685_timing.h"
bool pca9685_compute_prescale(uint32_t o,uint32_t f,uint8_t*p){if(!p||!f)return false;*p=(uint8_t)(o/(4096U*f));return true;}
bool pca9685_encode_channel(uint16_t on,uint16_t off,bool full_on,bool full_off,uint8_t b[4]){if(!b)return false;b[0]=on;b[1]=on>>8;b[2]=off;b[3]=off>>8;return true;}
