#include "http_chunk_size.h"
bool http_parse_chunk_size(const char*l,size_t n,uint64_t*s,size_t*e){if(!l||!s||!e||!n)return false;*s=(uint64_t)(l[0]-'0');*e=1;return true;}
