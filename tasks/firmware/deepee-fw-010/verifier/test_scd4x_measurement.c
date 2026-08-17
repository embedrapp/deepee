#include "scd4x_measurement.h"
#include <stdio.h>
#include <stdlib.h>
static uint8_t crc(const uint8_t*p){uint8_t c=0xff;for(int b=0;b<2;b++){c^=p[b];for(int i=0;i<8;i++)c=(c&0x80)?(uint8_t)((c<<1)^0x31):(uint8_t)(c<<1);}return c;}
static void req(int ok,const char*m){if(!ok){fprintf(stderr,"%s\n",m);exit(1);}}
static void word(uint8_t*p,uint16_t v){p[0]=(uint8_t)(v>>8);p[1]=(uint8_t)v;p[2]=crc(p);}
int main(void){uint8_t r[9];word(r,500);word(r+3,0);word(r+6,65535);SCD4xMeasurement m={0};
  req(scd4x_decode_measurement(r,&m),"valid response rejected");req(m.co2_ppm==500&&m.temperature_millic==-45000&&m.humidity_millipercent==100000,"endpoint conversion wrong");
  word(r+3,32768);word(r+6,32768);req(scd4x_decode_measurement(r,&m),"midscale rejected");req(m.temperature_millic==42501&&m.humidity_millipercent==50000,"midscale conversion wrong");
  r[5]^=1;m.co2_ppm=42;req(!scd4x_decode_measurement(r,&m)&&m.co2_ppm==42,"CRC failure accepted or output changed");req(!scd4x_decode_measurement(0,&m),"null input accepted");return 0;}
