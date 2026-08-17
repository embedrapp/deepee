#include "utf8_decode.h"
#include <stdio.h>
#include <stdlib.h>
static void req(int o,const char*m){if(!o){fprintf(stderr,"%s\n",m);exit(1);}}
int main(void){uint32_t s=9;size_t c=9;uint8_t a[]={'A'};req(utf8_decode_one(a,1,&s,&c)&&s==65&&c==1,"ASCII wrong");uint8_t e[]={0xe2,0x82,0xac};req(utf8_decode_one(e,3,&s,&c)&&s==0x20ac&&c==3,"three-byte wrong");uint8_t f[]={0xf0,0x9f,0x98,0x80};req(utf8_decode_one(f,4,&s,&c)&&s==0x1f600&&c==4,"four-byte wrong");uint8_t over[]={0xc0,0x80};s=7;c=8;req(!utf8_decode_one(over,2,&s,&c)&&s==7&&c==8,"overlong accepted or outputs changed");uint8_t sur[]={0xed,0xa0,0x80};req(!utf8_decode_one(sur,3,&s,&c),"surrogate accepted");uint8_t high[]={0xf4,0x90,0x80,0x80};req(!utf8_decode_one(high,4,&s,&c),"out-of-range scalar accepted");return 0;}
