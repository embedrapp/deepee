# Repair strict Base64 decoding

Repair `firmware/src/base64_decode.c`. Decode the RFC 4648 base alphabet in
complete four-character quanta. Permit zero, one, or two terminal padding
characters only where valid. Reject whitespace, misplaced padding, invalid
alphabet bytes, non-zero discarded pad bits, incomplete quanta, and output
overflow. Leave `output_length` unchanged on failure.
