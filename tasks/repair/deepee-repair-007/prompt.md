# Repair CBOR unsigned-integer parsing

Repair `firmware/src/cbor_uint.c`. Parse one major-type-zero CBOR unsigned
integer, including additional-information forms 24, 25, 26, and 27 in
network byte order. Reject truncated values, other major types, reserved
additional information, and non-shortest encodings. Report bytes consumed
and leave outputs untouched on failure.
