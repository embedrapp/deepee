# Repair strict UTF-8 decoding

Repair `firmware/src/utf8_decode.c` so it decodes exactly one Unicode scalar
value and reports bytes consumed. Accept ASCII and valid two-, three-, and
four-byte sequences. Reject missing/invalid continuation bytes, overlong
forms, surrogate code points, U+110000 and above, and the prohibited leading
bytes C0, C1, and F5..FF. Leave outputs unchanged on failure.
