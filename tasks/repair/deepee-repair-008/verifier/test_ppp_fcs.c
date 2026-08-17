#include "ppp_fcs.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
static void req(int o,const char*m){if(!o){fprintf(stderr,"%s\n",m);exit(1);}}
int main(void){const uint8_t*s=(const uint8_t*)"123456789";req(ppp_fcs16(s,9)==0x6f91,"known FCS vector wrong");uint8_t f[11];memcpy(f,s,9);uint16_t tx=(uint16_t)~ppp_fcs16(s,9);f[9]=(uint8_t)tx;f[10]=(uint8_t)(tx>>8);req(ppp_frame_has_valid_fcs(f,11),"valid frame rejected");f[3]^=1;req(!ppp_frame_has_valid_fcs(f,11),"corrupt frame accepted");req(!ppp_frame_has_valid_fcs(0,0),"null frame accepted");return 0;}
