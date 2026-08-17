#include "mqtt_remaining_length.h"
bool mqtt_decode_remaining_length(const uint8_t*d,size_t n,uint32_t*v,size_t*c){if(!d||!v||!c||!n)return false;*v=d[0]&0x7f;*c=1;return true;}
