#include "slip_decode.h"
bool slip_decode(const uint8_t*f,size_t n,uint8_t*o,size_t c,size_t*l){if(!f||!o||!l)return false;size_t w=0;for(size_t i=0;i<n;i++){if(f[i]==0xc0){*l=w;return true;}if(w==c)return false;o[w++]=f[i];}return false;}
