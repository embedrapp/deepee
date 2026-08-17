# Validate and decode a DS18B20 scratchpad

Implement `src/ds18b20_scratchpad.c` for the temperature-probe driver.
Verify the Dallas/Maxim CRC-8 over bytes 0..7 before using the frame.
Decode the signed temperature word, apply the resolution selected by
configuration bits 6:5 by clearing undefined low bits, and return the
temperature in microdegrees Celsius plus the 9..12-bit resolution.

A failed CRC or null argument must return false without changing either
output. Keep the protected API and integration files unchanged.
