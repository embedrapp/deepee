#include <Arduino.h>
extern "C" {
#include "bmp280_temperature.h"
}
void setup(void) { Serial.begin(115200); }
void loop(void) { delay(1000); }
