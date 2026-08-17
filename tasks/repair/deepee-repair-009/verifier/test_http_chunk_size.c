#include "http_chunk_size.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
static void req(int o,const char*m){if(!o){fprintf(stderr,"%s\n",m);exit(1);}}
int main(void){uint64_t s=9;size_t e=9;const char*a="1a\r\n";req(http_parse_chunk_size(a,4,&s,&e)&&s==26&&e==2,"plain size wrong");const char*b="A;foo=bar\r\n";req(http_parse_chunk_size(b,11,&s,&e)&&s==10&&e==1,"extension wrong");const char*mx="ffffffffffffffff\r\n";req(http_parse_chunk_size(mx,18,&s,&e)&&s==UINT64_MAX,"maximum wrong");s=7;e=8;const char*ov="10000000000000000\r\n";req(!http_parse_chunk_size(ov,19,&s,&e)&&s==7&&e==8,"overflow accepted or outputs changed");const char*bare="1\n";req(!http_parse_chunk_size(bare,2,&s,&e),"bare LF accepted");const char*empty=";x\r\n";req(!http_parse_chunk_size(empty,4,&s,&e),"missing digits accepted");return 0;}
