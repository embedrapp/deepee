# Task sources and selection

Tasks were selected from real public engineering evidence, then reduced to bounded fixtures that can be verified offline.

| Task | Real source | Benchmark adaptation |
|---|---|---|
| Rollover scheduler repair | Espressif Arduino-ESP32 issue #2430 | Isolates rollover-safe deadline comparison and cadence preservation in C. |
| ESP32-S2 I²C recovery | Espressif Arduino-ESP32 issue #8480 | Preserves the reported pins, addresses, clock rates, and recovery sequence; native tests make the policy deterministic. |
| Wrapped byte ring buffer | Zephyr ring-buffer API documentation | Exercises ordered partial reads/writes across the storage boundary without copying Zephyr source. |
| Overflow-safe ADC scaling | Zephyr ADC helper documentation | Requires widened intermediate arithmetic, rounding, input validation, and final range checks. |
| SHT3x measurement decoding | Sensirion SHT3x-DIS datasheet | Covers the published CRC-8 and raw temperature/humidity conversion contracts. |
| BME280 temperature compensation | Bosch BME280 datasheet and official SensorAPI | Covers the documented integer compensation path and `t_fine` result. |
| Modbus RTU CRC | Modbus Organization serial-line guide | Covers the published CRC-16 initialization, polynomial, and byte-order contract. |
| MCP9808 register decoding | Microchip MCP9808 datasheet | Covers alert-bit masking, sign extension, and the published 0.0625 °C resolution. |
| Schematic repair | KiCad's official `ground_pin_test_error.kicad_sch` QA fixture | Requires fixing the actual swapped power-pin orientation and passing a fresh netlist/ERC check. |
| nRF24 routing | MIT-licensed `pilinux/nRF24breakoutBoard`, also present in PCBench | Redraws the practical module/header/decoupling topology in KiCad 10 and removes selected routes. |
| MCP9808 schematic design | Microchip's MCP9808 datasheet plus the published Adafruit breakout and Raspberry Pi example | Fixes the MPN, package, address straps, I²C pull-ups, connector, and pin contract; drawing geometry remains free. |
| MCP9808 PCB design | Same published breakout use case | Fixes the footprint/pad/outline contract; placement and routing geometry remain free. |

The task structure follows two useful findings from recent hardware-agent benchmarks: use real open-source design contexts and score completed boards with the EDA engine. PCBWorld reports 679 real open-source KiCad boards and evaluates connectivity/DRC from the completed board file; DeepEE adopts that engine-grounded feasibility principle but keeps version 1.1 binary and much smaller.

Direct sources are linked in each task's `SOURCE.md`.

The expanded assignments add official source material for INA219, BMP280,
ADS1115, DS18B20, SCD4x, PCA9685, MAX31855, AP2112, USB Type-C, MAX3485,
SN65HVD230, PCA9306, microSD, and NE555, plus the RFC/OASIS definitions for
SLIP, MQTT Remaining Length, UTF-8, CBOR, PPP FCS, HTTP chunking, and Base64.
Each exact primary-source URL is recorded beside the task it supports.

The [comma.ai harness tester challenge](https://github.com/commaai/harness_tester_challenge)
informed the presentation pattern: start from a believable product need, expose
native schematic/PCB/firmware artifacts, and make each failure consequential to
operation. No comma.ai design file or challenge answer is copied into these tasks.
