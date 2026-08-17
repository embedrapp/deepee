#include "cbor_uint.h"
bool cbor_decode_uint(const uint8_t*d,size_t n,uint64_t*v,size_t*c){if(!d||!v||!c||!n)return false;*v=d[0]&31;*c=1;return true;}
