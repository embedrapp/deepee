#include "utf8_decode.h"
bool utf8_decode_one(const uint8_t*d,size_t n,uint32_t*s,size_t*c){if(!d||!s||!c||!n)return false;*s=d[0];*c=1;return true;}
