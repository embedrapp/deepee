#include "mqtt_remaining_length.h"
#include <stdio.h>
#include <stdlib.h>
static void req(int o,const char*m){if(!o){fprintf(stderr,"%s\n",m);exit(1);}}
int main(void){uint32_t v=9;size_t c=9;uint8_t a[]={0x7f};req(mqtt_decode_remaining_length(a,1,&v,&c)&&v==127&&c==1,"one-byte decode wrong");uint8_t b[]={0xc1,0x02};req(mqtt_decode_remaining_length(b,2,&v,&c)&&v==321&&c==2,"two-byte decode wrong");uint8_t mx[]={0xff,0xff,0xff,0x7f};req(mqtt_decode_remaining_length(mx,4,&v,&c)&&v==268435455&&c==4,"maximum decode wrong");uint8_t trunc[]={0x80};v=7;c=8;req(!mqtt_decode_remaining_length(trunc,1,&v,&c)&&v==7&&c==8,"truncation accepted or outputs changed");uint8_t five[]={0x80,0x80,0x80,0x80,0};req(!mqtt_decode_remaining_length(five,5,&v,&c),"five-byte value accepted");return 0;}
