#include "max31855_decode.h"
static int32_t sign_extend(uint32_t value,unsigned bits){uint32_t sign=1U<<(bits-1);return (int32_t)((value^sign)-sign);}
bool max31855_decode(uint32_t f,MAX31855Reading*out){if(!out)return false;MAX31855Reading r={sign_extend(f>>18,14)*250000,sign_extend((f>>4)&0xfff,12)*62500,(f&(1U<<16))!=0,(f&4)!=0,(f&2)!=0,(f&1)!=0};*out=r;return true;}
