# Repair HTTP chunk-size parsing

Repair `firmware/src/http_chunk_size.c`. Parse one HTTP/1.1 chunk-size line:
one or more hexadecimal digits, an optional semicolon-prefixed extension,
then CRLF. Return the 64-bit chunk size and the offset of the semicolon (or
the CR position when no extension exists). Reject overflow, missing digits,
control bytes inside an extension, bare LF, and trailing data. Preserve
outputs on failure.
