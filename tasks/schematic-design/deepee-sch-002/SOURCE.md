# Task provenance

This greenfield design task is based on a real MCP9808 breakout use case, using the current production part and its documented pinout rather than copying an existing schematic.

- Microchip product and datasheet: https://www.microchip.com/en-us/product/MCP9808
- Adafruit MCP9808 breakout guide and PCB downloads: https://learn.adafruit.com/adafruit-mcp9808-precision-i2c-temperature-sensor-guide/downloads
- Raspberry Pi Pico MCP9808 example: https://github.com/raspberrypi/pico-examples/tree/master/i2c/mcp9808_i2c

The task contract is original project material. It includes the datasheet-required pull-up on the open-drain `ALERT` output. No third-party design file is included.
