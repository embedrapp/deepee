#include "http_chunk_size.h"
#include <stdint.h>
bool http_parse_chunk_size(const char*l,size_t n,uint64_t*s,size_t*e){if(!l||!s||!e||n<3||l[n-2]!='\r'||l[n-1]!='\n')return false;uint64_t v=0;size_t i=0;for(;i<n-2&&l[i]!=';';i++){unsigned d;if(l[i]>='0'&&l[i]<='9')d=l[i]-'0';else if(l[i]>='a'&&l[i]<='f')d=l[i]-'a'+10;else if(l[i]>='A'&&l[i]<='F')d=l[i]-'A'+10;else return false;if(v>(UINT64_MAX-d)/16)return false;v=v*16+d;}if(i==0)return false;size_t off=i;if(i<n-2){for(i++;i<n-2;i++){unsigned char ch=(unsigned char)l[i];if(ch<0x20||ch==0x7f)return false;}}*s=v;*e=off;return true;}
