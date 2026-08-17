#include "pca9685_timing.h"
bool pca9685_compute_prescale(uint32_t o,uint32_t f,uint8_t*p){
  if(!p||!o||!f)return false;uint64_t d=4096ULL*f;uint64_t q=(o+d/2)/d;if(q==0)return false;uint64_t v=q-1;if(v<3||v>255)return false;*p=(uint8_t)v;return true;}
bool pca9685_encode_channel(uint16_t on,uint16_t off,bool full_on,bool full_off,uint8_t b[4]){
  if(!b||on>4095||off>4095||(full_on&&full_off))return false;uint8_t v[4]={(uint8_t)on,(uint8_t)((on>>8)|(full_on?0x10:0)),(uint8_t)off,(uint8_t)((off>>8)|(full_off?0x10:0))};for(int i=0;i<4;i++)b[i]=v[i];return true;}
