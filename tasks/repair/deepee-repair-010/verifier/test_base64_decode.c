#include "base64_decode.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
static void req(int o,const char*m){if(!o){fprintf(stderr,"%s\n",m);exit(1);}}
int main(void){uint8_t o[8]={0};size_t n=9;req(base64_decode("Zm9v",4,o,8,&n)&&n==3&&!memcmp(o,"foo",3),"plain decode wrong");req(base64_decode("Zg==",4,o,8,&n)&&n==1&&o[0]=='f',"double padding wrong");req(base64_decode("Zm8=",4,o,8,&n)&&n==2&&!memcmp(o,"fo",2),"single padding wrong");n=7;req(!base64_decode("Zh==",4,o,8,&n)&&n==7,"noncanonical pad bits accepted or length changed");req(!base64_decode("Z m8",4,o,8,&n),"whitespace accepted");req(!base64_decode("Zm9v",4,o,2,&n),"overflow accepted");return 0;}
