#pragma once

#include "esphome/core/component.h"
#include "esphome/components/sensor/sensor.h"
#include "esphome/components/i2c/i2c.h"

namespace esphome {
namespace acd10 {

class ACD10Component : public PollingComponent, public i2c::I2CDevice {
 public:
  void set_co2_sensor(sensor::Sensor *co2) { co2_sensor_ = co2; }
  void set_temperature_sensor(sensor::Sensor *temperature_sensor) { temperature_sensor_ = temperature_sensor; }

  float get_setup_priority() const override;
  void setup() override;
  void dump_config() override;
  void update() override;

 protected:
  void read_serial_code(uint8_t *serial_number);
  void read_sensor();
  void read_firmware_version(uint8_t *firmware_version);
  uint8_t calc_crc8_(const uint8_t *buf, uint8_t len);
  sensor::Sensor *co2_sensor_;
  sensor::Sensor *temperature_sensor_;

  enum ErrorCode { NONE = 0, COMMUNICATION_FAILED, CRC_CHECK_FAILED, ACD10_NOT_READY } error_code_{NONE};
};

}  // namespace acd10
}  // namespace esphome
