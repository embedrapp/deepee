#ifndef DEEPEE_PPP_FCS_H
#define DEEPEE_PPP_FCS_H
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
uint16_t ppp_fcs16(const uint8_t *data,size_t length);
bool ppp_frame_has_valid_fcs(const uint8_t *frame,size_t length);
#endif
