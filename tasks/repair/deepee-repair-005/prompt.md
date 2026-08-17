# Repair MQTT Remaining Length decoding

Repair `firmware/src/mqtt_remaining_length.c`. Decode MQTT's base-128
Remaining Length field from at most four bytes. Report both the value and
number of bytes consumed. Reject truncated encodings, encodings that continue
past byte four, and values above 268,435,455. Do not change outputs on failure.
