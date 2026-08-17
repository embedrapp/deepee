#include "max31855_decode.h"
bool max31855_decode(uint32_t f,MAX31855Reading*out){if(!out)return false;out->thermocouple_microc=(int32_t)(f>>18)*250000;out->internal_microc=(int32_t)((f>>4)&0xfff)*62500;out->fault=(f&(1U<<16))!=0;out->short_vcc=(f&4)!=0;out->short_gnd=(f&2)!=0;out->open_circuit=(f&1)!=0;return true;}
