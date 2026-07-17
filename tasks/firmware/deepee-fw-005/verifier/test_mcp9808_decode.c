#include "mcp9808_decode.h"

#include <stdio.h>
#include <stdlib.h>

static void require_true(int value, const char *message) {
    if (!value) {
        fprintf(stderr, "%s\n", message);
        exit(1);
    }
}

int main(void) {
    MCP9808Reading reading;

    require_true(mcp9808_decode_ambient(0x0190U, &reading), "positive temperature was rejected");
    require_true(reading.temperature_microcelsius == 25000000, "positive temperature is wrong");
    require_true(!reading.critical_alert && !reading.upper_alert && !reading.lower_alert,
                 "clear alert flags decoded as set");

    require_true(mcp9808_decode_ambient(0x1F60U, &reading), "negative temperature was rejected");
    require_true(reading.temperature_microcelsius == -10000000, "negative temperature is wrong");

    require_true(mcp9808_decode_ambient(0xE190U, &reading), "flagged temperature was rejected");
    require_true(reading.temperature_microcelsius == 25000000, "flags changed temperature value");
    require_true(reading.critical_alert && reading.upper_alert && reading.lower_alert,
                 "alert flags were not preserved");

    require_true(mcp9808_decode_ambient(0x0001U, &reading), "fractional temperature was rejected");
    require_true(reading.temperature_microcelsius == 62500, "fractional resolution is wrong");
    require_true(mcp9808_decode_ambient(0x1FFFU, &reading), "negative fractional temperature rejected");
    require_true(reading.temperature_microcelsius == -62500, "negative fractional resolution is wrong");
    require_true(!mcp9808_decode_ambient(0U, 0), "null output was accepted");
    return 0;
}
