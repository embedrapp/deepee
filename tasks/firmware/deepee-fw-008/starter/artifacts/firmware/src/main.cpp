#include <Arduino.h>
extern "C" {
#include "ads1115_config.h"
}
void setup(void) { Serial.begin(115200); }
void loop(void) { delay(1000); }
