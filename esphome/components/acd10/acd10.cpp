#include "acd10.h"
#include "esphome/core/log.h"
#include "esphome/core/helpers.h"
#include "esphome/core/hal.h"

namespace esphome {
namespace acd10 {

static const char *const TAG = "acd10";

void ACD10Component::setup() {
  ESP_LOGCONFIG(TAG, "Setting up ACD10...");
  uint8_t serial_number[12];
  uint8_t firmware_version[12];
  this->read_serial_code(&serial_number[0]);
  this->read_firmware_version(&firmware_version[0]);
  ESP_LOGV(TAG, "    Serial Number: %s", serial_number);
  ESP_LOGV(TAG, "    Firmware Version: %s", firmware_version);

}

void ACD10Component::dump_config() {
  ESP_LOGCONFIG(TAG, "ACD10:");
  LOG_I2C_DEVICE(this);
  switch (this->error_code_) {
    case COMMUNICATION_FAILED:
      ESP_LOGE(TAG, "Communication with ACD10 failed!");
      break;
    case CRC_CHECK_FAILED:
      ESP_LOGE(TAG, "The crc check failed");
      break;
    case ACD10_NOT_READY:
      ESP_LOGE(TAG, "ACD10 CO2 sensor not ready, warming up...");
      break;
    case NONE:
    default:
      break;
  }
  LOG_UPDATE_INTERVAL(this);
  LOG_SENSOR("  ", "CO2", this->co2_sensor_);
}

float ACD10Component::get_setup_priority() const { return setup_priority::DATA; }

void ACD10Component::update() {
  uint32_t now_ms = millis();
  uint32_t warmup_ms = 10 * 1000;
  if (now_ms < warmup_ms) {
      ESP_LOGW(TAG, "ACD10 warming up, %" PRIu32 " s left", (warmup_ms - now_ms) / 1000);
      this->error_code_ = ACD10_NOT_READY;
      return;
  }
  read_sensor();
}

void ACD10Component::read_sensor() {
  uint8_t buf[2] = { 0x03, 0x00};
  this->write(buf, 2, true);
  delay(80);
  uint8_t data[10];
  this->read(data, 10);
  ESP_LOGV(TAG, "   RAW Sensor data: 0x%s", format_hex(data, 10).c_str());

  if(data[2] != this->calc_crc8_(&data[0], 2)) {
    this->error_code_ = CRC_CHECK_FAILED;
    return;
  }

  if(data[5] != this->calc_crc8_(&data[3], 2)) {
    this->error_code_ = CRC_CHECK_FAILED;
    return;
  }

  if(data[8] != this->calc_crc8_(&data[6], 2)) {
    this->error_code_ = CRC_CHECK_FAILED;
    return;
  }

  uint32_t co2;
  co2 = data[0];
  co2 <<= 8;
  co2 += data[1];
  co2 <<= 8;
  co2 += data[3];
  co2 <<= 8;
  co2 += data[4];

  uint16_t temperature_f;
  temperature_f = data[6];
  temperature_f <<= 8;
  temperature_f += data[7];

  float temperature = ((temperature_f / 100.0) - 32) / 1.8;

  ESP_LOGD(TAG, "Got temperature=%.2f°C co2=%.2fppm", temperature, co2);

  if (this->co2_sensor_ != nullptr)
    this->co2_sensor_->publish_state(co2);

  if (this->temperature_sensor_ != nullptr)
    this->temperature_sensor_->publish_state(temperature);
}

void ACD10Component::read_firmware_version(uint8_t *firmware_version) {
  uint8_t buf[2] = { 0xD1, 0x00};
  this->write(buf, 2, true);
  this->read(firmware_version, 12);
}

void ACD10Component::read_serial_code(uint8_t *serial_number) {
  uint8_t buf[2] = { 0xD2, 0x01};
  this->write(buf, 2, true);
  this->read(serial_number, 12);
}

uint8_t ACD10Component::calc_crc8_(const uint8_t *buf, uint8_t len) {

  uint8_t bit, byte, crc = 0xFF;
  for (byte=0; byte<len; byte++) {
    crc ^=(buf[byte]);
    for (bit=8; bit>0; --bit) {
      if(crc & 0x80)
        crc = (crc << 1) ^ 0x31;
      else
        crc = (crc << 1);
    }
  }
  return crc;
}
}  // namespace acd10
}  // namespace esphome
