#include "ds18b20_scratchpad.h"
#include <stdio.h>
#include <stdlib.h>
static uint8_t crc8(const uint8_t *d, unsigned n) { uint8_t c=0; while(n--){uint8_t v=*d++;for(int i=0;i<8;i++){uint8_t m=(c^v)&1;c>>=1;if(m)c^=0x8c;v>>=1;}}return c; }
static void req(int ok, const char *m) { if (!ok) { fprintf(stderr, "%s\n", m); exit(1); } }
int main(void) {
    uint8_t s[9] = {0x50,0x05,0,0,0x7f,0,0,0,0}; s[8]=crc8(s,8);
    int32_t t=0; uint8_t r=0;
    req(ds18b20_decode_scratchpad(s,&t,&r) && t==85000000 && r==12, "12-bit positive decode wrong");
    s[0]=0x5f; s[1]=0xff; s[4]=0x1f; s[8]=crc8(s,8);
    req(ds18b20_decode_scratchpad(s,&t,&r) && t==-10500000 && r==9, "9-bit signed/masking decode wrong");
    s[8]^=1; t=7; r=7; req(!ds18b20_decode_scratchpad(s,&t,&r) && t==7 && r==7, "bad CRC accepted or output changed");
    req(!ds18b20_decode_scratchpad(0,&t,&r), "null input accepted");
    return 0;
}
