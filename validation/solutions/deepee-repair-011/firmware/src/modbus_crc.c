#include "modbus_crc.h"
uint16_t modbus_crc16(const uint8_t*d,size_t n){uint16_t c=0xffff;if(!d&&n)return c;while(n--){c^=*d++;for(int i=0;i<8;i++)c=(c&1)?(uint16_t)((c>>1)^0xa001):(uint16_t)(c>>1);}return c;}
bool modbus_rtu_frame_valid(const uint8_t*f,size_t n){if(!f||n<3)return false;uint16_t c=modbus_crc16(f,n-2);return f[n-2]==(uint8_t)c&&f[n-1]==(uint8_t)(c>>8);}
