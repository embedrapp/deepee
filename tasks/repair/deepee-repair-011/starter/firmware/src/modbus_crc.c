#include "modbus_crc.h"
uint16_t modbus_crc16(const uint8_t*d,size_t n){uint16_t c=0;while(n--)c+=*d++;return c;}
bool modbus_rtu_frame_valid(const uint8_t*f,size_t n){return f&&n>2&&modbus_crc16(f,n-2)==(uint16_t)(f[n-2]<<8|f[n-1]);}
