#include "sht3x_decode.h"

#include <stdio.h>
#include <stdlib.h>

static void require_true(int value, const char *message) {
    if (!value) {
        fprintf(stderr, "%s\n", message);
        exit(1);
    }
}

static uint8_t reference_crc(const uint8_t *data, size_t length) {
    uint8_t crc = 0xFFU;
    for (size_t index = 0U; index < length; ++index) {
        crc ^= data[index];
        for (uint8_t bit = 0U; bit < 8U; ++bit) {
            crc = (crc & 0x80U) != 0U ? (uint8_t)((crc << 1U) ^ 0x31U) : (uint8_t)(crc << 1U);
        }
    }
    return crc;
}

static void make_frame(uint16_t temperature, uint16_t humidity, uint8_t frame[6]) {
    frame[0] = (uint8_t)(temperature >> 8U);
    frame[1] = (uint8_t)temperature;
    frame[2] = reference_crc(frame, 2U);
    frame[3] = (uint8_t)(humidity >> 8U);
    frame[4] = (uint8_t)humidity;
    frame[5] = reference_crc(frame + 3U, 2U);
}

int main(void) {
    const uint8_t documented[] = {0xBEU, 0xEFU};
    uint8_t frame[6];
    SHT3xMeasurement measurement;

    require_true(sht3x_crc8(documented, sizeof(documented)) == 0x92U, "documented CRC vector failed");
    make_frame(0U, 0U, frame);
    require_true(sht3x_decode_measurement(frame, &measurement), "minimum frame was rejected");
    require_true(measurement.temperature_millicelsius == -45000, "minimum temperature is wrong");
    require_true(measurement.humidity_millipercent == 0U, "minimum humidity is wrong");

    make_frame(0xFFFFU, 0xFFFFU, frame);
    require_true(sht3x_decode_measurement(frame, &measurement), "maximum frame was rejected");
    require_true(measurement.temperature_millicelsius == 130000, "maximum temperature is wrong");
    require_true(measurement.humidity_millipercent == 100000U, "maximum humidity is wrong");

    make_frame(0x6666U, 0x8000U, frame);
    require_true(sht3x_decode_measurement(frame, &measurement), "nominal frame was rejected");
    require_true(measurement.temperature_millicelsius == 25000, "nominal temperature is wrong");
    require_true(measurement.humidity_millipercent == 50001U, "rounded nominal humidity is wrong");

    frame[2] ^= 0x01U;
    require_true(!sht3x_decode_measurement(frame, &measurement), "bad temperature CRC was accepted");
    make_frame(0x6666U, 0x8000U, frame);
    frame[5] ^= 0x01U;
    require_true(!sht3x_decode_measurement(frame, &measurement), "bad humidity CRC was accepted");
    require_true(!sht3x_decode_measurement(frame, 0), "null output was accepted");
    return 0;
}
