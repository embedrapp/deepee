#include "base64_decode.h"
bool base64_decode(const char*i,size_t n,uint8_t*o,size_t c,size_t*l){(void)c;if(!i||!o||!l)return false;for(size_t x=0;x<n;x++)o[x]=(uint8_t)i[x];*l=n;return true;}
