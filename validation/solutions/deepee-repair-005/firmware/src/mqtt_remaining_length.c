#include "mqtt_remaining_length.h"
bool mqtt_decode_remaining_length(const uint8_t*d,size_t n,uint32_t*v,size_t*c){if(!d||!v||!c)return false;uint32_t x=0,m=1;for(size_t i=0;i<4;i++){if(i>=n)return false;uint8_t b=d[i];x+=(uint32_t)(b&0x7f)*m;if(!(b&0x80)){*v=x;*c=i+1;return true;}m*=128U;}return false;}
