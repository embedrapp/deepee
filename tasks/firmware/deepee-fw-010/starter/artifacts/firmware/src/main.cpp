#include <Arduino.h>
extern "C" {
#include "scd4x_measurement.h"
}
void setup(void) { Serial.begin(115200); }
void loop(void) { delay(1000); }
