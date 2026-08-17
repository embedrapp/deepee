#include "ppp_fcs.h"
uint16_t ppp_fcs16(const uint8_t*d,size_t n){uint16_t f=0xffff;if(!d&&n)return f;while(n--){f^=*d++;for(int i=0;i<8;i++)f=(f&1)?(uint16_t)((f>>1)^0x8408):(uint16_t)(f>>1);}return f;}
bool ppp_frame_has_valid_fcs(const uint8_t*f,size_t n){return f&&n>=2&&ppp_fcs16(f,n)==0xf0b8;}
