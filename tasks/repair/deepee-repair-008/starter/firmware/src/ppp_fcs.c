#include "ppp_fcs.h"
uint16_t ppp_fcs16(const uint8_t*d,size_t n){uint16_t f=0;while(n--)f+=*d++;return f;}
bool ppp_frame_has_valid_fcs(const uint8_t*f,size_t n){return n>=2&&ppp_fcs16(f,n)==0;}
