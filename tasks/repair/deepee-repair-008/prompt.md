# Repair PPP FCS calculation

Repair `firmware/src/ppp_fcs.c`. Implement the 16-bit PPP FCS with initial
value 0xFFFF and reversed polynomial 0x8408. `ppp_fcs16` returns the running
(uncomplemented) FCS. `ppp_frame_has_valid_fcs` checks a frame that already
includes its two transmitted, complemented, least-significant-byte-first FCS
octets against the good residue 0xF0B8.
