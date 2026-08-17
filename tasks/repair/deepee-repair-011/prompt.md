# Repair Modbus RTU CRC handling

Repair `firmware/src/modbus_crc.c`. Implement the Modbus RTU CRC-16 with
initial value 0xFFFF and reflected polynomial 0xA001. The frame validator
receives a complete RTU frame whose transmitted CRC low byte precedes its
high byte. It must reject null or undersized frames and detect any corruption.
