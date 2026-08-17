# Repair the SLIP frame decoder

The serial transport decoder mishandles escaped END/ESC bytes and can publish
partial frames after malformed input. Repair `firmware/src/slip_decode.c`.

Accept zero or more leading END bytes, require a terminating END, decode
ESC+ESC_END and ESC+ESC_ESC, and reject unknown or truncated escape sequences.
Reject output overflow. On failure, leave `output_length` unchanged.
