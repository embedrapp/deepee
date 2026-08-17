#include <Arduino.h>
extern "C" {
#include "pca9685_timing.h"
}
void setup(void) { Serial.begin(115200); }
void loop(void) { delay(1000); }
