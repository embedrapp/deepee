#include <Arduino.h>
extern "C" {
#include "ds18b20_scratchpad.h"
}
void setup(void) { Serial.begin(115200); }
void loop(void) { delay(1000); }
