#include "pca9685_timing.h"
#include <stdio.h>
#include <stdlib.h>
static void req(int o,const char*m){if(!o){fprintf(stderr,"%s\n",m);exit(1);}}
int main(void){uint8_t p=99,b[4]={9,9,9,9};req(pca9685_compute_prescale(25000000,50,&p)&&p==121,"50 Hz prescale wrong");req(pca9685_compute_prescale(25000000,1000,&p)&&p==5,"1 kHz prescale wrong");p=99;req(!pca9685_compute_prescale(25000000,100000,&p)&&p==99,"out-of-range prescale accepted");
  req(pca9685_encode_channel(0x123,0xabc,false,false,b)&&b[0]==0x23&&b[1]==1&&b[2]==0xbc&&b[3]==0x0a,"count encoding wrong");req(pca9685_encode_channel(0,0,true,false,b)&&b[1]==0x10,"full-on bit wrong");b[0]=7;req(!pca9685_encode_channel(4096,0,false,false,b)&&b[0]==7,"invalid count accepted or output changed");req(!pca9685_encode_channel(0,0,true,true,b),"conflicting full flags accepted");return 0;}
