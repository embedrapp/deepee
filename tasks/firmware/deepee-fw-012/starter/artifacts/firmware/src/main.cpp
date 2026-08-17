#include <Arduino.h>
extern "C" {
#include "max31855_decode.h"
}
void setup(void) { Serial.begin(115200); }
void loop(void) { delay(1000); }
