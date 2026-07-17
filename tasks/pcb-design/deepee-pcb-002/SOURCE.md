# Task provenance

This greenfield layout task uses the same real MCP9808 breakout application and official pinout as `deepee-sch-002`. The mechanical limit and fixed component contract are original benchmark requirements.

- Microchip product and datasheet: https://www.microchip.com/en-us/product/MCP9808
- Adafruit MCP9808 breakout guide and PCB downloads: https://learn.adafruit.com/adafruit-mcp9808-precision-i2c-temperature-sensor-guide/downloads
- Related real-board routing methodology: https://arxiv.org/abs/2607.05915

The board contract includes the datasheet-required pull-up on the open-drain `ALERT` output. No third-party board geometry or layout is included.
