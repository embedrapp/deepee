#!/usr/bin/env python3
"""Generate the additional firmware and embedded-C repair tasks.

The task text is deliberately written as an ordinary engineering handoff.  Source
links live in SOURCE.md so the electrical/protocol details remain auditable.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import shutil
import textwrap

import yaml


ROOT = Path(__file__).resolve().parents[1]
TASKS = ROOT / "tasks"
SOLUTIONS = ROOT / "validation" / "solutions"


def clean(text: str) -> str:
    # Triple-quoted Python fixtures contain a few C string/character escapes.
    # Restore those escapes after Python has decoded them.
    text = text.replace("\r\n", "\\r\\n")
    text = text.replace('"%s\n"', '"%s\\n"')
    text = text.replace("'\r'", "'\\r'")
    text = text.replace("'\n'", "'\\n'")
    text = text.replace('"1\n"', '"1\\n"')
    return textwrap.dedent(text).lstrip()


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


@dataclass(frozen=True)
class CodeTask:
    number: int
    slug: str
    title: str
    prompt: str
    source_note: str
    source_urls: tuple[str, ...]
    header: str
    starter: str
    solution: str
    tests: str
    firmware: bool = False

    @property
    def task_id(self) -> str:
        kind = "fw" if self.firmware else "repair"
        return f"deepee-{kind}-{self.number:03d}"

    @property
    def function_file(self) -> str:
        return f"{self.slug}.c"


FIRMWARE_TASKS = (
    CodeTask(
        6,
        "ina219_decode",
        "Decode INA219 measurement registers",
        clean("""
        # Decode INA219 measurement registers

        Finish `src/ina219_decode.c` for the current-monitor telemetry path.

        The shunt-voltage register is a signed 16-bit two's-complement value at
        10 µV per bit. In the bus-voltage register, bits 15:3 hold an unsigned
        measurement at 4 mV per bit, bit 1 is the conversion-ready flag, and
        bit 0 is the math-overflow flag. Return voltages in microvolts and
        preserve both flags.

        Reject a null output pointer. Do not change the header, `main.cpp`, or
        `platformio.ini`. Submit the completed C file in place; it must pass the
        native tests and the ESP32-S2 build.
        """),
        "Based on the INA219 register formats and conversion LSBs.",
        ("https://www.ti.com/lit/ds/symlink/ina219.pdf",),
        clean("""
        #ifndef DEEPEE_INA219_DECODE_H
        #define DEEPEE_INA219_DECODE_H
        #include <stdbool.h>
        #include <stdint.h>
        typedef struct {
            int32_t shunt_microvolts;
            uint32_t bus_microvolts;
            bool conversion_ready;
            bool math_overflow;
        } INA219Reading;
        bool ina219_decode(uint16_t shunt_register, uint16_t bus_register, INA219Reading *out);
        #endif
        """),
        clean("""
        #include "ina219_decode.h"
        bool ina219_decode(uint16_t shunt_register, uint16_t bus_register, INA219Reading *out) {
            if (out == 0) return false;
            out->shunt_microvolts = (int32_t)shunt_register * 10;
            out->bus_microvolts = (uint32_t)(bus_register >> 1) * 4000U;
            out->conversion_ready = (bus_register & 1U) != 0U;
            out->math_overflow = (bus_register & 2U) != 0U;
            return true;
        }
        """),
        clean("""
        #include "ina219_decode.h"
        bool ina219_decode(uint16_t shunt_register, uint16_t bus_register, INA219Reading *out) {
            if (out == 0) return false;
            out->shunt_microvolts = (int32_t)(int16_t)shunt_register * 10;
            out->bus_microvolts = (uint32_t)(bus_register >> 3) * 4000U;
            out->conversion_ready = (bus_register & 2U) != 0U;
            out->math_overflow = (bus_register & 1U) != 0U;
            return true;
        }
        """),
        clean("""
        #include "ina219_decode.h"
        #include <stdio.h>
        #include <stdlib.h>
        static void req(int ok, const char *m) { if (!ok) { fprintf(stderr, "%s\n", m); exit(1); } }
        int main(void) {
            INA219Reading r;
            req(ina219_decode(0x0064, (uint16_t)((3000U << 3) | 2U), &r), "nominal decode failed");
            req(r.shunt_microvolts == 1000 && r.bus_microvolts == 12000000U, "voltage decode wrong");
            req(r.conversion_ready && !r.math_overflow, "status decode wrong");
            req(ina219_decode(0xFF9C, 1U, &r), "negative decode failed");
            req(r.shunt_microvolts == -1000 && r.math_overflow && !r.conversion_ready, "signed/status decode wrong");
            req(!ina219_decode(0, 0, 0), "null output accepted");
            return 0;
        }
        """),
        True,
    ),
    CodeTask(
        7,
        "bmp280_temperature",
        "Implement BMP280 temperature compensation",
        clean("""
        # Implement BMP280 temperature compensation

        Complete `src/bmp280_temperature.c` using Bosch's integer compensation
        algorithm. The function receives the uncompensated 20-bit temperature
        reading and calibration coefficients `dig_T1`, `dig_T2`, and `dig_T3`.
        Return temperature in hundredths of a degree Celsius and also return
        `t_fine`, because the pressure path consumes it later.

        Match the datasheet's signed arithmetic and shift order exactly. Reject
        null output pointers and raw ADC values outside 0..0xFFFFF. Do not change
        the protected integration files.
        """),
        "Based on the BMP280 integer temperature-compensation formula.",
        ("https://www.bosch-sensortec.com/media/boschsensortec/downloads/datasheets/bst-bmp280-ds001.pdf",),
        clean("""
        #ifndef DEEPEE_BMP280_TEMPERATURE_H
        #define DEEPEE_BMP280_TEMPERATURE_H
        #include <stdbool.h>
        #include <stdint.h>
        bool bmp280_compensate_temperature(int32_t adc_t, uint16_t dig_t1, int16_t dig_t2,
                                           int16_t dig_t3, int32_t *temperature_centi_c,
                                           int32_t *t_fine);
        #endif
        """),
        clean("""
        #include "bmp280_temperature.h"
        bool bmp280_compensate_temperature(int32_t adc_t, uint16_t dig_t1, int16_t dig_t2,
                                           int16_t dig_t3, int32_t *temperature_centi_c,
                                           int32_t *t_fine) {
            (void)dig_t3;
            if (!temperature_centi_c || !t_fine) return false;
            int32_t var1 = (((adc_t >> 3) - ((int32_t)dig_t1 << 1)) * dig_t2) >> 11;
            *t_fine = var1;
            *temperature_centi_c = (var1 * 5 + 128) >> 8;
            return true;
        }
        """),
        clean("""
        #include "bmp280_temperature.h"
        bool bmp280_compensate_temperature(int32_t adc_t, uint16_t dig_t1, int16_t dig_t2,
                                           int16_t dig_t3, int32_t *temperature_centi_c,
                                           int32_t *t_fine) {
            if (!temperature_centi_c || !t_fine || adc_t < 0 || adc_t > 0xFFFFF) return false;
            int32_t var1 = ((((adc_t >> 3) - ((int32_t)dig_t1 << 1))) * (int32_t)dig_t2) >> 11;
            int32_t delta = (adc_t >> 4) - (int32_t)dig_t1;
            int32_t var2 = (int32_t)((((int64_t)delta * delta) >> 12) * dig_t3 >> 14);
            int32_t fine = var1 + var2;
            *t_fine = fine;
            *temperature_centi_c = (fine * 5 + 128) >> 8;
            return true;
        }
        """),
        clean("""
        #include "bmp280_temperature.h"
        #include <stdio.h>
        #include <stdlib.h>
        static void req(int ok, const char *m) { if (!ok) { fprintf(stderr, "%s\n", m); exit(1); } }
        int main(void) {
            int32_t t = 0, fine = 0;
            req(bmp280_compensate_temperature(519888, 27504, 26435, -1000, &t, &fine), "datasheet vector rejected");
            req(t == 2508 && fine == 128422, "datasheet vector wrong");
            req(bmp280_compensate_temperature(0, 27504, 26435, -1000, &t, &fine), "zero raw rejected");
            req(t == -14088, "cold-range signed arithmetic wrong");
            req(!bmp280_compensate_temperature(-1, 1, 1, 1, &t, &fine), "negative raw accepted");
            req(!bmp280_compensate_temperature(0, 1, 1, 1, 0, &fine), "null output accepted");
            return 0;
        }
        """),
        True,
    ),
    CodeTask(
        8,
        "ads1115_config",
        "Build ADS1115 configuration words",
        clean("""
        # Build ADS1115 configuration words

        Complete `src/ads1115_config.c`. Construct a configuration register for
        a fresh conversion using the caller's MUX, PGA, data-rate, conversion
        mode, and comparator-enable selections. Set OS to start a conversion.
        Comparator mode, polarity, and latching remain at their default zero
        values; COMP_QUE is `00` when enabled and `11` when disabled.

        Accept MUX 0..7, PGA 0..5, and data rate 0..7. Reject invalid fields or
        a null destination without modifying the destination.
        """),
        "Based on the ADS1115 configuration-register bit fields.",
        ("https://www.ti.com/lit/ds/symlink/ads1115.pdf",),
        clean("""
        #ifndef DEEPEE_ADS1115_CONFIG_H
        #define DEEPEE_ADS1115_CONFIG_H
        #include <stdbool.h>
        #include <stdint.h>
        bool ads1115_build_config(uint8_t mux, uint8_t pga, uint8_t data_rate,
                                  bool continuous, bool comparator_enable, uint16_t *config);
        #endif
        """),
        clean("""
        #include "ads1115_config.h"
        bool ads1115_build_config(uint8_t mux, uint8_t pga, uint8_t data_rate,
                                  bool continuous, bool comparator_enable, uint16_t *config) {
            if (!config) return false;
            *config = (uint16_t)(0x8000U | ((uint16_t)mux << 11) | ((uint16_t)pga << 8) |
                                 ((uint16_t)data_rate << 4) | (continuous ? 0U : 0x0100U) |
                                 (comparator_enable ? 0U : 3U));
            return true;
        }
        """),
        clean("""
        #include "ads1115_config.h"
        bool ads1115_build_config(uint8_t mux, uint8_t pga, uint8_t data_rate,
                                  bool continuous, bool comparator_enable, uint16_t *config) {
            if (!config || mux > 7U || pga > 5U || data_rate > 7U) return false;
            uint16_t value = 0x8000U;
            value |= (uint16_t)mux << 12;
            value |= (uint16_t)pga << 9;
            if (!continuous) value |= 0x0100U;
            value |= (uint16_t)data_rate << 5;
            value |= comparator_enable ? 0U : 3U;
            *config = value;
            return true;
        }
        """),
        clean("""
        #include "ads1115_config.h"
        #include <stdio.h>
        #include <stdlib.h>
        static void req(int ok, const char *m) { if (!ok) { fprintf(stderr, "%s\n", m); exit(1); } }
        int main(void) {
            uint16_t v = 0;
            req(ads1115_build_config(4, 2, 4, false, false, &v), "single-shot config rejected");
            req(v == 0xC583U, "single-shot config wrong");
            req(ads1115_build_config(7, 5, 7, true, true, &v), "continuous config rejected");
            req(v == 0xFAE0U, "continuous config wrong");
            v = 0x1234;
            req(!ads1115_build_config(0, 6, 0, false, false, &v) && v == 0x1234, "invalid PGA accepted or output changed");
            req(!ads1115_build_config(0, 0, 8, false, false, &v), "invalid rate accepted");
            req(!ads1115_build_config(0, 0, 0, false, false, 0), "null output accepted");
            return 0;
        }
        """),
        True,
    ),
    CodeTask(
        9,
        "ds18b20_scratchpad",
        "Validate and decode a DS18B20 scratchpad",
        clean("""
        # Validate and decode a DS18B20 scratchpad

        Implement `src/ds18b20_scratchpad.c` for the temperature-probe driver.
        Verify the Dallas/Maxim CRC-8 over bytes 0..7 before using the frame.
        Decode the signed temperature word, apply the resolution selected by
        configuration bits 6:5 by clearing undefined low bits, and return the
        temperature in microdegrees Celsius plus the 9..12-bit resolution.

        A failed CRC or null argument must return false without changing either
        output. Keep the protected API and integration files unchanged.
        """),
        "Based on the DS18B20 scratchpad, resolution, temperature, and CRC definitions.",
        ("https://www.analog.com/media/en/technical-documentation/data-sheets/ds18b20.pdf",),
        clean("""
        #ifndef DEEPEE_DS18B20_SCRATCHPAD_H
        #define DEEPEE_DS18B20_SCRATCHPAD_H
        #include <stdbool.h>
        #include <stdint.h>
        bool ds18b20_decode_scratchpad(const uint8_t scratchpad[9], int32_t *temperature_microc,
                                       uint8_t *resolution_bits);
        #endif
        """),
        clean("""
        #include "ds18b20_scratchpad.h"
        bool ds18b20_decode_scratchpad(const uint8_t s[9], int32_t *temperature_microc,
                                       uint8_t *resolution_bits) {
            if (!s || !temperature_microc || !resolution_bits) return false;
            int16_t raw = (int16_t)((uint16_t)s[0] | ((uint16_t)s[1] << 8));
            *temperature_microc = raw * 62500;
            *resolution_bits = 12;
            return true;
        }
        """),
        clean("""
        #include "ds18b20_scratchpad.h"
        static uint8_t crc8(const uint8_t *data, unsigned length) {
            uint8_t crc = 0;
            while (length--) {
                uint8_t value = *data++;
                for (unsigned i = 0; i < 8; ++i) {
                    uint8_t mix = (uint8_t)((crc ^ value) & 1U);
                    crc >>= 1;
                    if (mix) crc ^= 0x8CU;
                    value >>= 1;
                }
            }
            return crc;
        }
        bool ds18b20_decode_scratchpad(const uint8_t s[9], int32_t *temperature_microc,
                                       uint8_t *resolution_bits) {
            if (!s || !temperature_microc || !resolution_bits || crc8(s, 8) != s[8]) return false;
            uint8_t resolution = (uint8_t)(9U + ((s[4] >> 5) & 3U));
            int16_t raw = (int16_t)((uint16_t)s[0] | ((uint16_t)s[1] << 8));
            unsigned undefined = 12U - resolution;
            raw = (int16_t)(raw & (int16_t)~((1U << undefined) - 1U));
            *temperature_microc = (int32_t)raw * 62500;
            *resolution_bits = resolution;
            return true;
        }
        """),
        clean("""
        #include "ds18b20_scratchpad.h"
        #include <stdio.h>
        #include <stdlib.h>
        static uint8_t crc8(const uint8_t *d, unsigned n) { uint8_t c=0; while(n--){uint8_t v=*d++;for(int i=0;i<8;i++){uint8_t m=(c^v)&1;c>>=1;if(m)c^=0x8c;v>>=1;}}return c; }
        static void req(int ok, const char *m) { if (!ok) { fprintf(stderr, "%s\n", m); exit(1); } }
        int main(void) {
            uint8_t s[9] = {0x50,0x05,0,0,0x7f,0,0,0,0}; s[8]=crc8(s,8);
            int32_t t=0; uint8_t r=0;
            req(ds18b20_decode_scratchpad(s,&t,&r) && t==85000000 && r==12, "12-bit positive decode wrong");
            s[0]=0x5f; s[1]=0xff; s[4]=0x1f; s[8]=crc8(s,8);
            req(ds18b20_decode_scratchpad(s,&t,&r) && t==-10500000 && r==9, "9-bit signed/masking decode wrong");
            s[8]^=1; t=7; r=7; req(!ds18b20_decode_scratchpad(s,&t,&r) && t==7 && r==7, "bad CRC accepted or output changed");
            req(!ds18b20_decode_scratchpad(0,&t,&r), "null input accepted");
            return 0;
        }
        """),
        True,
    ),
    CodeTask(
        10,
        "scd4x_measurement",
        "Decode an SCD4x measurement response",
        clean("""
        # Decode an SCD4x measurement response

        Complete `src/scd4x_measurement.c`. A measurement response contains
        three big-endian 16-bit words—CO2, temperature, and relative humidity—
        with a CRC byte after each word. Validate every CRC using polynomial
        0x31 and initial value 0xFF.

        Return CO2 in ppm, temperature in millidegrees Celsius using
        `-45 + 175 * raw / 65535`, and humidity in milli-percent RH using
        `100 * raw / 65535`. Use integer arithmetic and reject null pointers or
        any CRC failure without modifying the output.
        """),
        "Based on Sensirion's SCD4x data-word CRC and measurement conversion formulas.",
        ("https://sensirion.com/media/documents/48C4B7FB/67FE0194/CD_DS_SCD4x_Datasheet_D1.pdf",),
        clean("""
        #ifndef DEEPEE_SCD4X_MEASUREMENT_H
        #define DEEPEE_SCD4X_MEASUREMENT_H
        #include <stdbool.h>
        #include <stdint.h>
        typedef struct { uint16_t co2_ppm; int32_t temperature_millic; uint32_t humidity_millipercent; } SCD4xMeasurement;
        bool scd4x_decode_measurement(const uint8_t response[9], SCD4xMeasurement *out);
        #endif
        """),
        clean("""
        #include "scd4x_measurement.h"
        bool scd4x_decode_measurement(const uint8_t r[9], SCD4xMeasurement *out) {
            if (!r || !out) return false;
            out->co2_ppm = (uint16_t)((r[0] << 8) | r[1]);
            out->temperature_millic = -45000 + (175000 * (int32_t)((r[3] << 8) | r[4])) / 65536;
            out->humidity_millipercent = (100000U * (uint32_t)((r[6] << 8) | r[7])) / 65536U;
            return true;
        }
        """),
        clean("""
        #include "scd4x_measurement.h"
        static uint8_t crc_word(const uint8_t *p) {
            uint8_t crc = 0xFF;
            for (unsigned b=0;b<2;b++) { crc ^= p[b]; for (unsigned i=0;i<8;i++) crc = (crc & 0x80U) ? (uint8_t)((crc << 1) ^ 0x31U) : (uint8_t)(crc << 1); }
            return crc;
        }
        bool scd4x_decode_measurement(const uint8_t r[9], SCD4xMeasurement *out) {
            if (!r || !out || crc_word(r)!=r[2] || crc_word(r+3)!=r[5] || crc_word(r+6)!=r[8]) return false;
            uint16_t co2=(uint16_t)((r[0]<<8)|r[1]);
            uint16_t tr=(uint16_t)((r[3]<<8)|r[4]);
            uint16_t hr=(uint16_t)((r[6]<<8)|r[7]);
            SCD4xMeasurement value = { co2, -45000 + (int32_t)((175000LL*tr)/65535LL), (uint32_t)((100000ULL*hr)/65535ULL) };
            *out=value;
            return true;
        }
        """),
        clean("""
        #include "scd4x_measurement.h"
        #include <stdio.h>
        #include <stdlib.h>
        static uint8_t crc(const uint8_t*p){uint8_t c=0xff;for(int b=0;b<2;b++){c^=p[b];for(int i=0;i<8;i++)c=(c&0x80)?(uint8_t)((c<<1)^0x31):(uint8_t)(c<<1);}return c;}
        static void req(int ok,const char*m){if(!ok){fprintf(stderr,"%s\n",m);exit(1);}}
        static void word(uint8_t*p,uint16_t v){p[0]=(uint8_t)(v>>8);p[1]=(uint8_t)v;p[2]=crc(p);}
        int main(void){uint8_t r[9];word(r,500);word(r+3,0);word(r+6,65535);SCD4xMeasurement m={0};
          req(scd4x_decode_measurement(r,&m),"valid response rejected");req(m.co2_ppm==500&&m.temperature_millic==-45000&&m.humidity_millipercent==100000,"endpoint conversion wrong");
          word(r+3,32768);word(r+6,32768);req(scd4x_decode_measurement(r,&m),"midscale rejected");req(m.temperature_millic==42501&&m.humidity_millipercent==50000,"midscale conversion wrong");
          r[5]^=1;m.co2_ppm=42;req(!scd4x_decode_measurement(r,&m)&&m.co2_ppm==42,"CRC failure accepted or output changed");req(!scd4x_decode_measurement(0,&m),"null input accepted");return 0;}
        """),
        True,
    ),
    CodeTask(
        11,
        "pca9685_timing",
        "Implement PCA9685 timing helpers",
        clean("""
        # Implement PCA9685 timing helpers

        Finish `src/pca9685_timing.c`. Compute the PRE_SCALE register from the
        oscillator frequency and requested PWM frequency by rounding
        `oscillator / (4096 * frequency)` to the nearest integer and subtracting
        one. Only register values 3..255 are usable.

        Also encode one channel's 12-bit ON and OFF counts into the four LED
        register bytes, including the full-on and full-off bits. Counts above
        4095 and simultaneous full-on/full-off requests are invalid. Failed
        calls must not modify their destination.
        """),
        "Based on the PCA9685 prescale equation and LEDn register layout.",
        ("https://www.nxp.com/docs/en/data-sheet/PCA9685.pdf",),
        clean("""
        #ifndef DEEPEE_PCA9685_TIMING_H
        #define DEEPEE_PCA9685_TIMING_H
        #include <stdbool.h>
        #include <stdint.h>
        bool pca9685_compute_prescale(uint32_t oscillator_hz, uint32_t pwm_hz, uint8_t *prescale);
        bool pca9685_encode_channel(uint16_t on, uint16_t off, bool full_on, bool full_off, uint8_t bytes[4]);
        #endif
        """),
        clean("""
        #include "pca9685_timing.h"
        bool pca9685_compute_prescale(uint32_t o,uint32_t f,uint8_t*p){if(!p||!f)return false;*p=(uint8_t)(o/(4096U*f));return true;}
        bool pca9685_encode_channel(uint16_t on,uint16_t off,bool full_on,bool full_off,uint8_t b[4]){if(!b)return false;b[0]=on;b[1]=on>>8;b[2]=off;b[3]=off>>8;return true;}
        """),
        clean("""
        #include "pca9685_timing.h"
        bool pca9685_compute_prescale(uint32_t oscillator_hz, uint32_t pwm_hz, uint8_t *prescale) {
          if (!prescale || !oscillator_hz || !pwm_hz) return false;
          uint64_t denominator = 4096ULL * pwm_hz;
          uint64_t rounded_ratio = (oscillator_hz + denominator / 2) / denominator;
          if (rounded_ratio == 0) return false;
          uint64_t value = rounded_ratio - 1;
          if (value < 3 || value > 255) return false;
          *prescale = (uint8_t)value;
          return true;
        }
        bool pca9685_encode_channel(uint16_t on, uint16_t off, bool full_on, bool full_off, uint8_t bytes[4]) {
          if (!bytes || on > 4095 || off > 4095 || (full_on && full_off)) return false;
          const uint8_t encoded[4] = {
            (uint8_t)on,
            (uint8_t)((on >> 8) | (full_on ? 0x10 : 0)),
            (uint8_t)off,
            (uint8_t)((off >> 8) | (full_off ? 0x10 : 0)),
          };
          for (int index = 0; index < 4; ++index) bytes[index] = encoded[index];
          return true;
        }
        """),
        clean("""
        #include "pca9685_timing.h"
        #include <stdio.h>
        #include <stdlib.h>
        static void req(int o,const char*m){if(!o){fprintf(stderr,"%s\n",m);exit(1);}}
        int main(void){uint8_t p=99,b[4]={9,9,9,9};req(pca9685_compute_prescale(25000000,50,&p)&&p==121,"50 Hz prescale wrong");req(pca9685_compute_prescale(25000000,1000,&p)&&p==5,"1 kHz prescale wrong");p=99;req(!pca9685_compute_prescale(25000000,100000,&p)&&p==99,"out-of-range prescale accepted");
          req(pca9685_encode_channel(0x123,0xabc,false,false,b)&&b[0]==0x23&&b[1]==1&&b[2]==0xbc&&b[3]==0x0a,"count encoding wrong");req(pca9685_encode_channel(0,0,true,false,b)&&b[1]==0x10,"full-on bit wrong");b[0]=7;req(!pca9685_encode_channel(4096,0,false,false,b)&&b[0]==7,"invalid count accepted or output changed");req(!pca9685_encode_channel(0,0,true,true,b),"conflicting full flags accepted");return 0;}
        """),
        True,
    ),
    CodeTask(
        12,
        "max31855_decode",
        "Decode MAX31855 thermocouple frames",
        clean("""
        # Decode MAX31855 thermocouple frames

        Complete `src/max31855_decode.c`. Decode the signed 14-bit
        thermocouple field in bits 31:18 and the signed 12-bit internal
        temperature field in bits 15:4. Return both in microdegrees Celsius;
        their LSBs are 0.25 °C and 0.0625 °C respectively.

        Preserve the general fault flag in bit 16 and the short-to-VCC,
        short-to-ground, and open-circuit flags in bits 2:0. Reject a null
        destination without writing anything.
        """),
        "Based on the MAX31855 32-bit read format, signed fields, and fault flags.",
        ("https://www.analog.com/media/en/technical-documentation/data-sheets/MAX31855.pdf",),
        clean("""
        #ifndef DEEPEE_MAX31855_DECODE_H
        #define DEEPEE_MAX31855_DECODE_H
        #include <stdbool.h>
        #include <stdint.h>
        typedef struct { int32_t thermocouple_microc; int32_t internal_microc; bool fault; bool short_vcc; bool short_gnd; bool open_circuit; } MAX31855Reading;
        bool max31855_decode(uint32_t frame, MAX31855Reading *out);
        #endif
        """),
        clean("""
        #include "max31855_decode.h"
        bool max31855_decode(uint32_t f,MAX31855Reading*out){if(!out)return false;out->thermocouple_microc=(int32_t)(f>>18)*250000;out->internal_microc=(int32_t)((f>>4)&0xfff)*62500;out->fault=(f&(1U<<16))!=0;out->short_vcc=(f&4)!=0;out->short_gnd=(f&2)!=0;out->open_circuit=(f&1)!=0;return true;}
        """),
        clean("""
        #include "max31855_decode.h"
        static int32_t sign_extend(uint32_t value,unsigned bits){uint32_t sign=1U<<(bits-1);return (int32_t)((value^sign)-sign);}
        bool max31855_decode(uint32_t f,MAX31855Reading*out){if(!out)return false;MAX31855Reading r={sign_extend(f>>18,14)*250000,sign_extend((f>>4)&0xfff,12)*62500,(f&(1U<<16))!=0,(f&4)!=0,(f&2)!=0,(f&1)!=0};*out=r;return true;}
        """),
        clean("""
        #include "max31855_decode.h"
        #include <stdio.h>
        #include <stdlib.h>
        static void req(int o,const char*m){if(!o){fprintf(stderr,"%s\n",m);exit(1);}}
        int main(void){MAX31855Reading r;uint32_t f=(100U<<18)|(400U<<4);req(max31855_decode(f,&r),"positive frame rejected");req(r.thermocouple_microc==25000000&&r.internal_microc==25000000,"positive values wrong");
          f=((uint32_t)(0x3fffU-39U)<<18)|((uint32_t)(0xfffU-15U)<<4)|(1U<<16)|5U;req(max31855_decode(f,&r),"negative frame rejected");req(r.thermocouple_microc==-10000000&&r.internal_microc==-1000000,"signed values wrong");req(r.fault&&r.short_vcc&&!r.short_gnd&&r.open_circuit,"fault flags wrong");req(!max31855_decode(0,0),"null output accepted");return 0;}
        """),
        True,
    ),
)


REPAIR_TASKS = (
    CodeTask(4, "slip_decode", "Repair a SLIP frame decoder", clean("""
    # Repair the SLIP frame decoder

    The serial transport decoder mishandles escaped END/ESC bytes and can publish
    partial frames after malformed input. Repair `firmware/src/slip_decode.c`.

    Accept zero or more leading END bytes, require a terminating END, decode
    ESC+ESC_END and ESC+ESC_ESC, and reject unknown or truncated escape sequences.
    Reject output overflow. On failure, leave `output_length` unchanged.
    """), "Based on RFC 1055 SLIP framing and byte stuffing.", ("https://www.rfc-editor.org/rfc/rfc1055.html",),
    clean("""#ifndef DEEPEE_SLIP_DECODE_H
#define DEEPEE_SLIP_DECODE_H
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
bool slip_decode(const uint8_t *frame,size_t length,uint8_t *output,size_t capacity,size_t *output_length);
#endif
"""),
    clean("""#include "slip_decode.h"
bool slip_decode(const uint8_t*f,size_t n,uint8_t*o,size_t c,size_t*l){if(!f||!o||!l)return false;size_t w=0;for(size_t i=0;i<n;i++){if(f[i]==0xc0){*l=w;return true;}if(w==c)return false;o[w++]=f[i];}return false;}
"""),
    clean("""#include "slip_decode.h"
bool slip_decode(const uint8_t*f,size_t n,uint8_t*o,size_t c,size_t*l){if(!f||!o||!l)return false;size_t i=0,w=0;while(i<n&&f[i]==0xc0)i++;for(;i<n;i++){uint8_t b=f[i];if(b==0xc0){if(w==0)continue;*l=w;return true;}if(b==0xdb){if(++i>=n)return false;if(f[i]==0xdc)b=0xc0;else if(f[i]==0xdd)b=0xdb;else return false;}if(w>=c)return false;o[w++]=b;}return false;}
"""),
    clean("""#include "slip_decode.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
static void req(int o,const char*m){if(!o){fprintf(stderr,"%s\n",m);exit(1);}}
int main(void){uint8_t in[]={0xc0,1,0xdb,0xdc,2,0xdb,0xdd,0xc0};uint8_t out[4]={0};size_t n=99;req(slip_decode(in,sizeof in,out,sizeof out,&n),"valid frame rejected");uint8_t exp[]={1,0xc0,2,0xdb};req(n==4&&!memcmp(out,exp,4),"escape decode wrong");uint8_t bad[]={1,0xdb,2,0xc0};n=77;req(!slip_decode(bad,sizeof bad,out,4,&n)&&n==77,"bad escape accepted or length changed");uint8_t longf[]={1,2,3,0xc0};req(!slip_decode(longf,sizeof longf,out,2,&n),"overflow accepted");req(!slip_decode(in,3,out,4,&n),"unterminated frame accepted");return 0;}
""")),
    CodeTask(5, "mqtt_remaining_length", "Repair MQTT Remaining Length decoding", clean("""
    # Repair MQTT Remaining Length decoding

    Repair `firmware/src/mqtt_remaining_length.c`. Decode MQTT's base-128
    Remaining Length field from at most four bytes. Report both the value and
    number of bytes consumed. Reject truncated encodings, encodings that continue
    past byte four, and values above 268,435,455. Do not change outputs on failure.
    """), "Based on MQTT 5.0 section 2.1.4.", ("https://docs.oasis-open.org/mqtt/mqtt/v5.0/mqtt-v5.0.html",),
    clean("""#ifndef DEEPEE_MQTT_REMAINING_LENGTH_H
#define DEEPEE_MQTT_REMAINING_LENGTH_H
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
bool mqtt_decode_remaining_length(const uint8_t *data,size_t length,uint32_t *value,size_t *consumed);
#endif
"""),
    clean("""#include "mqtt_remaining_length.h"
bool mqtt_decode_remaining_length(const uint8_t*d,size_t n,uint32_t*v,size_t*c){if(!d||!v||!c||!n)return false;*v=d[0]&0x7f;*c=1;return true;}
"""),
    clean("""#include "mqtt_remaining_length.h"
bool mqtt_decode_remaining_length(const uint8_t*d,size_t n,uint32_t*v,size_t*c){if(!d||!v||!c)return false;uint32_t x=0,m=1;for(size_t i=0;i<4;i++){if(i>=n)return false;uint8_t b=d[i];x+=(uint32_t)(b&0x7f)*m;if(!(b&0x80)){*v=x;*c=i+1;return true;}m*=128U;}return false;}
"""),
    clean("""#include "mqtt_remaining_length.h"
#include <stdio.h>
#include <stdlib.h>
static void req(int o,const char*m){if(!o){fprintf(stderr,"%s\n",m);exit(1);}}
int main(void){uint32_t v=9;size_t c=9;uint8_t a[]={0x7f};req(mqtt_decode_remaining_length(a,1,&v,&c)&&v==127&&c==1,"one-byte decode wrong");uint8_t b[]={0xc1,0x02};req(mqtt_decode_remaining_length(b,2,&v,&c)&&v==321&&c==2,"two-byte decode wrong");uint8_t mx[]={0xff,0xff,0xff,0x7f};req(mqtt_decode_remaining_length(mx,4,&v,&c)&&v==268435455&&c==4,"maximum decode wrong");uint8_t trunc[]={0x80};v=7;c=8;req(!mqtt_decode_remaining_length(trunc,1,&v,&c)&&v==7&&c==8,"truncation accepted or outputs changed");uint8_t five[]={0x80,0x80,0x80,0x80,0};req(!mqtt_decode_remaining_length(five,5,&v,&c),"five-byte value accepted");return 0;}
""")),
    CodeTask(6, "utf8_decode", "Repair strict UTF-8 decoding", clean("""
    # Repair strict UTF-8 decoding

    Repair `firmware/src/utf8_decode.c` so it decodes exactly one Unicode scalar
    value and reports bytes consumed. Accept ASCII and valid two-, three-, and
    four-byte sequences. Reject missing/invalid continuation bytes, overlong
    forms, surrogate code points, U+110000 and above, and the prohibited leading
    bytes C0, C1, and F5..FF. Leave outputs unchanged on failure.
    """), "Based on RFC 3629's UTF-8 syntax and validity constraints.", ("https://www.rfc-editor.org/rfc/rfc3629.html",),
    clean("""#ifndef DEEPEE_UTF8_DECODE_H
#define DEEPEE_UTF8_DECODE_H
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
bool utf8_decode_one(const uint8_t *data,size_t length,uint32_t *scalar,size_t *consumed);
#endif
"""),
    clean("""#include "utf8_decode.h"
bool utf8_decode_one(const uint8_t*d,size_t n,uint32_t*s,size_t*c){if(!d||!s||!c||!n)return false;*s=d[0];*c=1;return true;}
"""),
    clean("""#include "utf8_decode.h"
bool utf8_decode_one(const uint8_t*d,size_t n,uint32_t*s,size_t*c){if(!d||!s||!c||!n)return false;uint32_t cp;size_t k;if(d[0]<0x80){cp=d[0];k=1;}else if(d[0]>=0xc2&&d[0]<=0xdf){cp=d[0]&0x1f;k=2;}else if(d[0]>=0xe0&&d[0]<=0xef){cp=d[0]&0x0f;k=3;}else if(d[0]>=0xf0&&d[0]<=0xf4){cp=d[0]&7;k=4;}else return false;if(n<k)return false;for(size_t i=1;i<k;i++){if((d[i]&0xc0)!=0x80)return false;cp=(cp<<6)|(d[i]&0x3f);}if((k==2&&cp<0x80)||(k==3&&cp<0x800)||(k==4&&cp<0x10000)||(cp>=0xd800&&cp<=0xdfff)||cp>0x10ffff)return false;*s=cp;*c=k;return true;}
"""),
    clean("""#include "utf8_decode.h"
#include <stdio.h>
#include <stdlib.h>
static void req(int o,const char*m){if(!o){fprintf(stderr,"%s\n",m);exit(1);}}
int main(void){uint32_t s=9;size_t c=9;uint8_t a[]={'A'};req(utf8_decode_one(a,1,&s,&c)&&s==65&&c==1,"ASCII wrong");uint8_t e[]={0xe2,0x82,0xac};req(utf8_decode_one(e,3,&s,&c)&&s==0x20ac&&c==3,"three-byte wrong");uint8_t f[]={0xf0,0x9f,0x98,0x80};req(utf8_decode_one(f,4,&s,&c)&&s==0x1f600&&c==4,"four-byte wrong");uint8_t over[]={0xc0,0x80};s=7;c=8;req(!utf8_decode_one(over,2,&s,&c)&&s==7&&c==8,"overlong accepted or outputs changed");uint8_t sur[]={0xed,0xa0,0x80};req(!utf8_decode_one(sur,3,&s,&c),"surrogate accepted");uint8_t high[]={0xf4,0x90,0x80,0x80};req(!utf8_decode_one(high,4,&s,&c),"out-of-range scalar accepted");return 0;}
""")),
    CodeTask(7, "cbor_uint", "Repair CBOR unsigned-integer parsing", clean("""
    # Repair CBOR unsigned-integer parsing

    Repair `firmware/src/cbor_uint.c`. Parse one major-type-zero CBOR unsigned
    integer, including additional-information forms 24, 25, 26, and 27 in
    network byte order. Reject truncated values, other major types, reserved
    additional information, and non-shortest encodings. Report bytes consumed
    and leave outputs untouched on failure.
    """), "Based on RFC 8949 sections 3 and 3.1.", ("https://www.rfc-editor.org/rfc/rfc8949.html",),
    clean("""#ifndef DEEPEE_CBOR_UINT_H
#define DEEPEE_CBOR_UINT_H
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
bool cbor_decode_uint(const uint8_t *data,size_t length,uint64_t *value,size_t *consumed);
#endif
"""),
    clean("""#include "cbor_uint.h"
bool cbor_decode_uint(const uint8_t*d,size_t n,uint64_t*v,size_t*c){if(!d||!v||!c||!n)return false;*v=d[0]&31;*c=1;return true;}
"""),
    clean("""#include "cbor_uint.h"
bool cbor_decode_uint(const uint8_t*d,size_t n,uint64_t*v,size_t*c){if(!d||!v||!c||!n||(d[0]>>5)!=0)return false;uint8_t a=d[0]&31;uint64_t x;size_t k;if(a<24){x=a;k=1;}else{size_t bytes=a==24?1:a==25?2:a==26?4:a==27?8:0;if(!bytes||n<1+bytes)return false;x=0;for(size_t i=0;i<bytes;i++)x=(x<<8)|d[1+i];if((bytes==1&&x<24)||(bytes==2&&x<=0xff)||(bytes==4&&x<=0xffff)||(bytes==8&&x<=0xffffffffULL))return false;k=1+bytes;}*v=x;*c=k;return true;}
"""),
    clean("""#include "cbor_uint.h"
#include <stdio.h>
#include <stdlib.h>
static void req(int o,const char*m){if(!o){fprintf(stderr,"%s\n",m);exit(1);}}
int main(void){uint64_t v=9;size_t c=9;uint8_t a[]={23};req(cbor_decode_uint(a,1,&v,&c)&&v==23&&c==1,"immediate wrong");uint8_t b[]={0x19,0x03,0xe8};req(cbor_decode_uint(b,3,&v,&c)&&v==1000&&c==3,"16-bit wrong");uint8_t q[]={0x1b,0x01,0,0,0,0,0,0,0};req(cbor_decode_uint(q,9,&v,&c)&&v==0x0100000000000000ULL,"64-bit wrong");uint8_t non[]={0x18,0x17};v=7;c=8;req(!cbor_decode_uint(non,2,&v,&c)&&v==7&&c==8,"non-shortest accepted or outputs changed");uint8_t neg[]={0x20};req(!cbor_decode_uint(neg,1,&v,&c),"other major type accepted");uint8_t trunc[]={0x1a,1};req(!cbor_decode_uint(trunc,2,&v,&c),"truncated value accepted");return 0;}
""")),
    CodeTask(8, "ppp_fcs", "Repair PPP FCS calculation", clean("""
    # Repair PPP FCS calculation

    Repair `firmware/src/ppp_fcs.c`. Implement the 16-bit PPP FCS with initial
    value 0xFFFF and reversed polynomial 0x8408. `ppp_fcs16` returns the running
    (uncomplemented) FCS. `ppp_frame_has_valid_fcs` checks a frame that already
    includes its two transmitted, complemented, least-significant-byte-first FCS
    octets against the good residue 0xF0B8.
    """), "Based on RFC 1662 appendices C.2 and C.3.", ("https://www.rfc-editor.org/rfc/rfc1662.html",),
    clean("""#ifndef DEEPEE_PPP_FCS_H
#define DEEPEE_PPP_FCS_H
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
uint16_t ppp_fcs16(const uint8_t *data,size_t length);
bool ppp_frame_has_valid_fcs(const uint8_t *frame,size_t length);
#endif
"""),
    clean("""#include "ppp_fcs.h"
uint16_t ppp_fcs16(const uint8_t*d,size_t n){uint16_t f=0;while(n--)f+=*d++;return f;}
bool ppp_frame_has_valid_fcs(const uint8_t*f,size_t n){return n>=2&&ppp_fcs16(f,n)==0;}
"""),
    clean("""#include "ppp_fcs.h"
uint16_t ppp_fcs16(const uint8_t*d,size_t n){uint16_t f=0xffff;if(!d&&n)return f;while(n--){f^=*d++;for(int i=0;i<8;i++)f=(f&1)?(uint16_t)((f>>1)^0x8408):(uint16_t)(f>>1);}return f;}
bool ppp_frame_has_valid_fcs(const uint8_t*f,size_t n){return f&&n>=2&&ppp_fcs16(f,n)==0xf0b8;}
"""),
    clean("""#include "ppp_fcs.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
static void req(int o,const char*m){if(!o){fprintf(stderr,"%s\n",m);exit(1);}}
int main(void){const uint8_t*s=(const uint8_t*)"123456789";req(ppp_fcs16(s,9)==0x6f91,"known FCS vector wrong");uint8_t f[11];memcpy(f,s,9);uint16_t tx=(uint16_t)~ppp_fcs16(s,9);f[9]=(uint8_t)tx;f[10]=(uint8_t)(tx>>8);req(ppp_frame_has_valid_fcs(f,11),"valid frame rejected");f[3]^=1;req(!ppp_frame_has_valid_fcs(f,11),"corrupt frame accepted");req(!ppp_frame_has_valid_fcs(0,0),"null frame accepted");return 0;}
""")),
    CodeTask(9, "http_chunk_size", "Repair HTTP chunk-size parsing", clean("""
    # Repair HTTP chunk-size parsing

    Repair `firmware/src/http_chunk_size.c`. Parse one HTTP/1.1 chunk-size line:
    one or more hexadecimal digits, an optional semicolon-prefixed extension,
    then CRLF. Return the 64-bit chunk size and the offset of the semicolon (or
    the CR position when no extension exists). Reject overflow, missing digits,
    control bytes inside an extension, bare LF, and trailing data. Preserve
    outputs on failure.
    """), "Based on RFC 9112 sections 7.1 and 7.1.1.", ("https://www.rfc-editor.org/rfc/rfc9112.html",),
    clean("""#ifndef DEEPEE_HTTP_CHUNK_SIZE_H
#define DEEPEE_HTTP_CHUNK_SIZE_H
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
bool http_parse_chunk_size(const char *line,size_t length,uint64_t *size,size_t *extension_offset);
#endif
"""),
    clean("""#include "http_chunk_size.h"
bool http_parse_chunk_size(const char*l,size_t n,uint64_t*s,size_t*e){if(!l||!s||!e||!n)return false;*s=(uint64_t)(l[0]-'0');*e=1;return true;}
"""),
    clean("""#include "http_chunk_size.h"
#include <stdint.h>
bool http_parse_chunk_size(const char*l,size_t n,uint64_t*s,size_t*e){if(!l||!s||!e||n<3||l[n-2]!='\r'||l[n-1]!='\n')return false;uint64_t v=0;size_t i=0;for(;i<n-2&&l[i]!=';';i++){unsigned d;if(l[i]>='0'&&l[i]<='9')d=l[i]-'0';else if(l[i]>='a'&&l[i]<='f')d=l[i]-'a'+10;else if(l[i]>='A'&&l[i]<='F')d=l[i]-'A'+10;else return false;if(v>(UINT64_MAX-d)/16)return false;v=v*16+d;}if(i==0)return false;size_t off=i;if(i<n-2){for(i++;i<n-2;i++){unsigned char ch=(unsigned char)l[i];if(ch<0x20||ch==0x7f)return false;}}*s=v;*e=off;return true;}
"""),
    clean("""#include "http_chunk_size.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
static void req(int o,const char*m){if(!o){fprintf(stderr,"%s\n",m);exit(1);}}
int main(void){uint64_t s=9;size_t e=9;const char*a="1a\r\n";req(http_parse_chunk_size(a,4,&s,&e)&&s==26&&e==2,"plain size wrong");const char*b="A;foo=bar\r\n";req(http_parse_chunk_size(b,11,&s,&e)&&s==10&&e==1,"extension wrong");const char*mx="ffffffffffffffff\r\n";req(http_parse_chunk_size(mx,18,&s,&e)&&s==UINT64_MAX,"maximum wrong");s=7;e=8;const char*ov="10000000000000000\r\n";req(!http_parse_chunk_size(ov,19,&s,&e)&&s==7&&e==8,"overflow accepted or outputs changed");const char*bare="1\n";req(!http_parse_chunk_size(bare,2,&s,&e),"bare LF accepted");const char*empty=";x\r\n";req(!http_parse_chunk_size(empty,4,&s,&e),"missing digits accepted");return 0;}
""")),
    CodeTask(10, "base64_decode", "Repair strict Base64 decoding", clean("""
    # Repair strict Base64 decoding

    Repair `firmware/src/base64_decode.c`. Decode the RFC 4648 base alphabet in
    complete four-character quanta. Permit zero, one, or two terminal padding
    characters only where valid. Reject whitespace, misplaced padding, invalid
    alphabet bytes, non-zero discarded pad bits, incomplete quanta, and output
    overflow. Leave `output_length` unchanged on failure.
    """), "Based on RFC 4648 sections 3.2, 3.5, and 4.", ("https://www.rfc-editor.org/rfc/rfc4648.html",),
    clean("""#ifndef DEEPEE_BASE64_DECODE_H
#define DEEPEE_BASE64_DECODE_H
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
bool base64_decode(const char *input,size_t length,uint8_t *output,size_t capacity,size_t *output_length);
#endif
"""),
    clean("""#include "base64_decode.h"
bool base64_decode(const char*i,size_t n,uint8_t*o,size_t c,size_t*l){(void)c;if(!i||!o||!l)return false;for(size_t x=0;x<n;x++)o[x]=(uint8_t)i[x];*l=n;return true;}
"""),
    clean("""#include "base64_decode.h"
static int val(char c){if(c>='A'&&c<='Z')return c-'A';if(c>='a'&&c<='z')return c-'a'+26;if(c>='0'&&c<='9')return c-'0'+52;if(c=='+')return 62;if(c=='/')return 63;return -1;}
bool base64_decode(const char*i,size_t n,uint8_t*o,size_t c,size_t*l){if(!i||!o||!l||n%4)return false;size_t w=0;for(size_t p=0;p<n;p+=4){int a=val(i[p]),b=val(i[p+1]);if(a<0||b<0)return false;int pad2=i[p+2]=='=',pad3=i[p+3]=='=';if(pad2&&!pad3)return false;if((pad2||pad3)&&p+4!=n)return false;int d2=pad2?0:val(i[p+2]),d3=pad3?0:val(i[p+3]);if(d2<0||d3<0)return false;if((pad2&&(b&15))||(pad3&&!pad2&&(d2&3)))return false;size_t need=pad2?1:pad3?2:3;if(w+need>c)return false;uint32_t v=(uint32_t)(a<<18|b<<12|d2<<6|d3);o[w++]=(uint8_t)(v>>16);if(need>1)o[w++]=(uint8_t)(v>>8);if(need>2)o[w++]=(uint8_t)v;}*l=w;return true;}
"""),
    clean("""#include "base64_decode.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
static void req(int o,const char*m){if(!o){fprintf(stderr,"%s\n",m);exit(1);}}
int main(void){uint8_t o[8]={0};size_t n=9;req(base64_decode("Zm9v",4,o,8,&n)&&n==3&&!memcmp(o,"foo",3),"plain decode wrong");req(base64_decode("Zg==",4,o,8,&n)&&n==1&&o[0]=='f',"double padding wrong");req(base64_decode("Zm8=",4,o,8,&n)&&n==2&&!memcmp(o,"fo",2),"single padding wrong");n=7;req(!base64_decode("Zh==",4,o,8,&n)&&n==7,"noncanonical pad bits accepted or length changed");req(!base64_decode("Z m8",4,o,8,&n),"whitespace accepted");req(!base64_decode("Zm9v",4,o,2,&n),"overflow accepted");return 0;}
""")),
    CodeTask(11, "modbus_crc", "Repair Modbus RTU CRC handling", clean("""
    # Repair Modbus RTU CRC handling

    Repair `firmware/src/modbus_crc.c`. Implement the Modbus RTU CRC-16 with
    initial value 0xFFFF and reflected polynomial 0xA001. The frame validator
    receives a complete RTU frame whose transmitted CRC low byte precedes its
    high byte. It must reject null or undersized frames and detect any corruption.
    """), "Based on the Modbus over Serial Line specification's CRC generation procedure.", ("https://www.modbus.org/docs/Modbus_over_serial_line_V1_02.pdf",),
    clean("""#ifndef DEEPEE_MODBUS_CRC_H
#define DEEPEE_MODBUS_CRC_H
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
uint16_t modbus_crc16(const uint8_t *data,size_t length);
bool modbus_rtu_frame_valid(const uint8_t *frame,size_t length);
#endif
"""),
    clean("""#include "modbus_crc.h"
uint16_t modbus_crc16(const uint8_t*d,size_t n){uint16_t c=0;while(n--)c+=*d++;return c;}
bool modbus_rtu_frame_valid(const uint8_t*f,size_t n){return f&&n>2&&modbus_crc16(f,n-2)==(uint16_t)(f[n-2]<<8|f[n-1]);}
"""),
    clean("""#include "modbus_crc.h"
uint16_t modbus_crc16(const uint8_t*d,size_t n){uint16_t c=0xffff;if(!d&&n)return c;while(n--){c^=*d++;for(int i=0;i<8;i++)c=(c&1)?(uint16_t)((c>>1)^0xa001):(uint16_t)(c>>1);}return c;}
bool modbus_rtu_frame_valid(const uint8_t*f,size_t n){if(!f||n<3)return false;uint16_t c=modbus_crc16(f,n-2);return f[n-2]==(uint8_t)c&&f[n-1]==(uint8_t)(c>>8);}
"""),
    clean("""#include "modbus_crc.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
static void req(int o,const char*m){if(!o){fprintf(stderr,"%s\n",m);exit(1);}}
int main(void){const uint8_t*s=(const uint8_t*)"123456789";req(modbus_crc16(s,9)==0x4b37,"known vector wrong");uint8_t f[]={1,3,0,0,0,2,0,0};uint16_t c=modbus_crc16(f,6);f[6]=(uint8_t)c;f[7]=(uint8_t)(c>>8);req(modbus_rtu_frame_valid(f,8),"valid frame rejected");f[2]^=1;req(!modbus_rtu_frame_valid(f,8),"corruption accepted");req(!modbus_rtu_frame_valid(0,0),"null frame accepted");return 0;}
""")),
    CodeTask(12, "time32", "Repair wrap-safe tick timing", clean("""
    # Repair wrap-safe tick timing

    Repair `firmware/src/time32.c` for a 32-bit millisecond tick counter that
    wraps naturally. `time32_deadline_reached` must treat `now` as on or after a
    deadline when their signed modular difference is nonnegative. Inputs are
    guaranteed to be separated by less than 2^31 ticks. `time32_elapsed` returns
    modular elapsed time. `time32_schedule_after` rejects a null destination or
    delays of 2^31 ticks and above, otherwise stores `now + delay` modulo 2^32.
    """), "Based on the Linux kernel's documented wrap-safe time comparison model.", ("https://docs.kernel.org/driver-api/basics.html#c.time_after",),
    clean("""#ifndef DEEPEE_TIME32_H
#define DEEPEE_TIME32_H
#include <stdbool.h>
#include <stdint.h>
bool time32_deadline_reached(uint32_t now,uint32_t deadline);
uint32_t time32_elapsed(uint32_t now,uint32_t then);
bool time32_schedule_after(uint32_t now,uint32_t delay,uint32_t *deadline);
#endif
"""),
    clean("""#include "time32.h"
bool time32_deadline_reached(uint32_t n,uint32_t d){return n>=d;}
uint32_t time32_elapsed(uint32_t n,uint32_t t){return n-t;}
bool time32_schedule_after(uint32_t n,uint32_t delay,uint32_t*d){if(!d)return false;*d=n+delay;return true;}
"""),
    clean("""#include "time32.h"
#include <limits.h>
bool time32_deadline_reached(uint32_t n,uint32_t d){return (int32_t)(n-d)>=0;}
uint32_t time32_elapsed(uint32_t n,uint32_t t){return n-t;}
bool time32_schedule_after(uint32_t n,uint32_t delay,uint32_t*d){if(!d||delay>INT32_MAX)return false;*d=n+delay;return true;}
"""),
    clean("""#include "time32.h"
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
static void req(int o,const char*m){if(!o){fprintf(stderr,"%s\n",m);exit(1);}}
int main(void){req(!time32_deadline_reached(99,100),"early time reached");req(time32_deadline_reached(100,100)&&time32_deadline_reached(101,100),"ordinary deadline wrong");req(!time32_deadline_reached(0xfffffff0U,0x10U),"pre-wrap time reached post-wrap deadline");req(time32_deadline_reached(0x20U,0xfffffff0U),"post-wrap deadline missed");req(time32_elapsed(0x10U,0xfffffff0U)==32U,"wrapped elapsed wrong");uint32_t d=7;req(time32_schedule_after(0xfffffff0U,32U,&d)&&d==0x10U,"wrapped schedule wrong");d=7;req(!time32_schedule_after(0,0x80000000U,&d)&&d==7,"ambiguous delay accepted or output changed");return 0;}
""")),
)


PLATFORMIO = clean("""
[env:esp32-s2]
platform = espressif32@6.10.0
board = esp32-s2-saola-1
framework = arduino
build_flags = -Iinclude
monitor_speed = 115200
""")


MAKEFILE = clean("""
CC ?= cc
CFLAGS ?= -std=c99 -Wall -Wextra -Werror
.PHONY: all clean
all: object.o
object.o: src/{slug}.c src/{slug}.h
	$(CC) $(CFLAGS) -c src/{slug}.c -o $@
clean:
	rm -f object.o
""")


def provenance(task: CodeTask) -> str:
    links = "\n".join(f"- {url}" for url in task.source_urls)
    return f"# Task provenance\n\n{task.source_note}\n\n{links}\n\nThe API, integration fixture, tests, and faulty starter implementation are original project material.\n"


def generate_firmware(task: CodeTask) -> None:
    base = TASKS / "firmware" / task.task_id
    solution = SOLUTIONS / task.task_id
    shutil.rmtree(base, ignore_errors=True)
    shutil.rmtree(solution, ignore_errors=True)
    root = "artifacts/firmware"
    write(base / "prompt.md", task.prompt)
    write(base / "SOURCE.md", provenance(task))
    write(base / "expected_artifacts.yaml", yaml.safe_dump({"required": [f"{root}/include/{task.slug}.h", f"{root}/src/{task.slug}.c", f"{root}/src/main.cpp", f"{root}/platformio.ini"]}, sort_keys=False))
    write(base / "starter" / root / "include" / f"{task.slug}.h", task.header)
    write(base / "starter" / root / "src" / f"{task.slug}.c", task.starter)
    write(base / "starter" / root / "src" / "main.cpp", f'#include <Arduino.h>\nextern "C" {{\n#include "{task.slug}.h"\n}}\nvoid setup(void) {{ Serial.begin(115200); }}\nvoid loop(void) {{ delay(1000); }}\n')
    write(base / "starter" / root / "platformio.ini", PLATFORMIO)
    write(base / "verifier" / f"test_{task.slug}.c", task.tests)
    write(solution / root / "src" / f"{task.slug}.c", task.solution)
    manifest = {
        "id": task.task_id, "suite": "firmware", "difficulty": "hard", "timeout_minutes": 60,
        "required_tools": ["gcc", "pio"], "submission_paths": [f"{root}/src/{task.slug}.c"],
        "required_artifacts": [{"path": f"{root}/platformio.ini", "kind": "file"}, {"path": f"{root}/include/{task.slug}.h", "kind": "file"}, {"path": f"{root}/src/{task.slug}.c", "kind": "file"}, {"path": f"{root}/src/main.cpp", "kind": "file"}],
        "checks": [
            {"type": "artifact_presence", "name": f"{task.slug}_project_complete"},
            {"type": "starter_integrity", "name": f"{task.slug}_integration_unchanged", "protected_globs": [f"{root}/include/{task.slug}.h", f"{root}/src/main.cpp", f"{root}/platformio.ini"]},
            {"type": "c_unit_tests", "name": f"{task.slug}_behavior", "sources": [f"{root}/src/{task.slug}.c"], "test_sources": [f"verifier/test_{task.slug}.c"], "include_dirs": [f"{root}/include"]},
            {"type": "firmware_build", "name": f"{task.slug}_esp32_s2_builds", "root": root, "allowed_build_systems": ["platformio"], "required_files": ["platformio.ini", "src/main.cpp", f"src/{task.slug}.c", f"include/{task.slug}.h"], "output_globs": [".pio/build/**/*.elf"], "timeout_seconds": 600},
        ],
    }
    write(base / "manifest.yaml", yaml.safe_dump(manifest, sort_keys=False))


def generate_repair(task: CodeTask) -> None:
    base = TASKS / "repair" / task.task_id
    solution = SOLUTIONS / task.task_id
    shutil.rmtree(base, ignore_errors=True)
    shutil.rmtree(solution, ignore_errors=True)
    root = "firmware"
    write(base / "prompt.md", task.prompt)
    write(base / "SOURCE.md", provenance(task))
    write(base / "expected_artifacts.yaml", yaml.safe_dump({"required": [f"{root}/src/{task.slug}.c"]}, sort_keys=False))
    write(base / "starter" / root / "src" / f"{task.slug}.h", task.header)
    write(base / "starter" / root / "src" / f"{task.slug}.c", task.starter)
    write(base / "starter" / root / "Makefile", MAKEFILE.format(slug=task.slug))
    write(base / "verifier" / f"test_{task.slug}.c", task.tests)
    write(solution / root / "src" / f"{task.slug}.c", task.solution)
    manifest = {
        "id": task.task_id, "suite": "repair", "difficulty": "hard", "timeout_minutes": 45,
        "required_tools": ["gcc"], "submission_paths": [f"{root}/src/{task.slug}.c"],
        "required_artifacts": [{"path": f"{root}/src/{task.slug}.c", "kind": "file"}],
        "checks": [
            {"type": "artifact_presence", "name": f"repaired_{task.slug}_exists"},
            {"type": "starter_integrity", "name": f"{task.slug}_contract_unchanged", "protected_globs": [f"{root}/src/{task.slug}.h", f"{root}/Makefile"]},
            {"type": "c_unit_tests", "name": f"{task.slug}_behavior", "sources": [f"{root}/src/{task.slug}.c"], "test_sources": [f"verifier/test_{task.slug}.c"], "include_dirs": [f"{root}/src"]},
        ],
    }
    write(base / "manifest.yaml", yaml.safe_dump(manifest, sort_keys=False))


def main() -> int:
    for task in FIRMWARE_TASKS:
        generate_firmware(task)
    for task in REPAIR_TASKS:
        generate_repair(task)
    print(f"Generated {len(FIRMWARE_TASKS)} firmware and {len(REPAIR_TASKS)} repair tasks")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
