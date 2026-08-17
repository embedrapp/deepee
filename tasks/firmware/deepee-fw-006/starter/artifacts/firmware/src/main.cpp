#include <Arduino.h>
extern "C" {
#include "ina219_decode.h"
}
void setup(void) { Serial.begin(115200); }
void loop(void) { delay(1000); }
