#include <Arduino.h>

extern "C" {
#include "mcp9808_decode.h"
}

void setup() {
    MCP9808Reading reading{};
    (void)mcp9808_decode_ambient(0x0190U, &reading);
}

void loop() {}
