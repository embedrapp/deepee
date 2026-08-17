#include "time32.h"
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
static void req(int o,const char*m){if(!o){fprintf(stderr,"%s\n",m);exit(1);}}
int main(void){req(!time32_deadline_reached(99,100),"early time reached");req(time32_deadline_reached(100,100)&&time32_deadline_reached(101,100),"ordinary deadline wrong");req(!time32_deadline_reached(0xfffffff0U,0x10U),"pre-wrap time reached post-wrap deadline");req(time32_deadline_reached(0x20U,0xfffffff0U),"post-wrap deadline missed");req(time32_elapsed(0x10U,0xfffffff0U)==32U,"wrapped elapsed wrong");uint32_t d=7;req(time32_schedule_after(0xfffffff0U,32U,&d)&&d==0x10U,"wrapped schedule wrong");d=7;req(!time32_schedule_after(0,0x80000000U,&d)&&d==7,"ambiguous delay accepted or output changed");return 0;}
