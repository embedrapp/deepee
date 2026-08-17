#include "max31855_decode.h"
#include <stdio.h>
#include <stdlib.h>
static void req(int o,const char*m){if(!o){fprintf(stderr,"%s\n",m);exit(1);}}
int main(void){MAX31855Reading r;uint32_t f=(100U<<18)|(400U<<4);req(max31855_decode(f,&r),"positive frame rejected");req(r.thermocouple_microc==25000000&&r.internal_microc==25000000,"positive values wrong");
  f=((uint32_t)(0x3fffU-39U)<<18)|((uint32_t)(0xfffU-15U)<<4)|(1U<<16)|5U;req(max31855_decode(f,&r),"negative frame rejected");req(r.thermocouple_microc==-10000000&&r.internal_microc==-1000000,"signed values wrong");req(r.fault&&r.short_vcc&&!r.short_gnd&&r.open_circuit,"fault flags wrong");req(!max31855_decode(0,0),"null output accepted");return 0;}
