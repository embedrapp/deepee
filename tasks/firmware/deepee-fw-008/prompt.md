# Build ADS1115 configuration words

Complete `src/ads1115_config.c`. Construct a configuration register for
a fresh conversion using the caller's MUX, PGA, data-rate, conversion
mode, and comparator-enable selections. Set OS to start a conversion.
Comparator mode, polarity, and latching remain at their default zero
values; COMP_QUE is `00` when enabled and `11` when disabled.

Accept MUX 0..7, PGA 0..5, and data rate 0..7. Reject invalid fields or
a null destination without modifying the destination.
