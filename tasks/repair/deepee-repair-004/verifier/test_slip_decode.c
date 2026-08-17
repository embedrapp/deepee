#include "slip_decode.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
static void req(int o,const char*m){if(!o){fprintf(stderr,"%s\n",m);exit(1);}}
int main(void){uint8_t in[]={0xc0,1,0xdb,0xdc,2,0xdb,0xdd,0xc0};uint8_t out[4]={0};size_t n=99;req(slip_decode(in,sizeof in,out,sizeof out,&n),"valid frame rejected");uint8_t exp[]={1,0xc0,2,0xdb};req(n==4&&!memcmp(out,exp,4),"escape decode wrong");uint8_t bad[]={1,0xdb,2,0xc0};n=77;req(!slip_decode(bad,sizeof bad,out,4,&n)&&n==77,"bad escape accepted or length changed");uint8_t longf[]={1,2,3,0xc0};req(!slip_decode(longf,sizeof longf,out,2,&n),"overflow accepted");req(!slip_decode(in,3,out,4,&n),"unterminated frame accepted");return 0;}
