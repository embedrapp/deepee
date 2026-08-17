#include "slip_decode.h"
bool slip_decode(const uint8_t*f,size_t n,uint8_t*o,size_t c,size_t*l){if(!f||!o||!l)return false;size_t i=0,w=0;while(i<n&&f[i]==0xc0)i++;for(;i<n;i++){uint8_t b=f[i];if(b==0xc0){if(w==0)continue;*l=w;return true;}if(b==0xdb){if(++i>=n)return false;if(f[i]==0xdc)b=0xc0;else if(f[i]==0xdd)b=0xdb;else return false;}if(w>=c)return false;o[w++]=b;}return false;}
