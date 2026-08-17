#include "modbus_crc.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
static void req(int o,const char*m){if(!o){fprintf(stderr,"%s\n",m);exit(1);}}
int main(void){const uint8_t*s=(const uint8_t*)"123456789";req(modbus_crc16(s,9)==0x4b37,"known vector wrong");uint8_t f[]={1,3,0,0,0,2,0,0};uint16_t c=modbus_crc16(f,6);f[6]=(uint8_t)c;f[7]=(uint8_t)(c>>8);req(modbus_rtu_frame_valid(f,8),"valid frame rejected");f[2]^=1;req(!modbus_rtu_frame_valid(f,8),"corruption accepted");req(!modbus_rtu_frame_valid(0,0),"null frame accepted");return 0;}
