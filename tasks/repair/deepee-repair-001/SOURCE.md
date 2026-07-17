# Task provenance

This compact repair task is adapted from the class of rollover failures documented in Espressif Arduino-ESP32 issue #2430, where millisecond arithmetic caused periodic timeout failures.

- Source issue: https://github.com/espressif/arduino-esp32/issues/2430
- Adaptation: the benchmark isolates rollover-safe comparison and cadence preservation behind a small C API with verifier-owned tests. No source code from the issue is copied.
