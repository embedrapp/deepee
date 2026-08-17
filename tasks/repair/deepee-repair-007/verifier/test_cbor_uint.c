#include "cbor_uint.h"
#include <stdio.h>
#include <stdlib.h>
static void req(int o,const char*m){if(!o){fprintf(stderr,"%s\n",m);exit(1);}}
int main(void){uint64_t v=9;size_t c=9;uint8_t a[]={23};req(cbor_decode_uint(a,1,&v,&c)&&v==23&&c==1,"immediate wrong");uint8_t b[]={0x19,0x03,0xe8};req(cbor_decode_uint(b,3,&v,&c)&&v==1000&&c==3,"16-bit wrong");uint8_t q[]={0x1b,0x01,0,0,0,0,0,0,0};req(cbor_decode_uint(q,9,&v,&c)&&v==0x0100000000000000ULL,"64-bit wrong");uint8_t non[]={0x18,0x17};v=7;c=8;req(!cbor_decode_uint(non,2,&v,&c)&&v==7&&c==8,"non-shortest accepted or outputs changed");uint8_t neg[]={0x20};req(!cbor_decode_uint(neg,1,&v,&c),"other major type accepted");uint8_t trunc[]={0x1a,1};req(!cbor_decode_uint(trunc,2,&v,&c),"truncated value accepted");return 0;}
