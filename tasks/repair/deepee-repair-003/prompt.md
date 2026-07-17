# Repair overflow-prone ADC scaling

The supplied ADC helper converts a signed raw sample into microvolts, but multiplies in 32 bits and silently wraps for legitimate inputs.

Repair `firmware/src/adc_scale.c` so that:

- valid resolutions are 1 through 30 bits and the reference must be positive;
- the result is `raw * reference_uv / 2^resolution`, with C integer division toward zero;
- negative differential samples are supported;
- intermediate arithmetic does not overflow;
- the function returns `false` for invalid arguments or when the mathematical result is outside `int32_t`;
- `output_uv` is written only on success.

Do not change `adc_scale.h` or the Makefile. Submit the repaired C file in place; verifier-owned native tests cover nominal, signed, boundary, and overflow cases.
