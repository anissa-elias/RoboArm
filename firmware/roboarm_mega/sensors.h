// Joint encoders (AS5600 analog) and TMC2209 UART drivers.
#pragma once
#include "config.h"

namespace sensors {

void begin();
void update();                    // non-blocking; samples encoders, polls one driver per call
float encoderDeg(uint8_t j);      // joint angle from the encoder, after zero offset
void zeroEncoders();              // current pose becomes zero; saved to EEPROM
bool driverOk(uint8_t j);         // UART answered (also means 24 V motor power is present)
uint16_t load(uint8_t j);         // StallGuard result (lower = more load), 0xFFFF if unknown
bool overTemp(uint8_t j);
bool openLoad(uint8_t j);
void setSgThreshold(uint8_t j, uint8_t thr);
uint8_t sgThreshold(uint8_t j);
void configureDrivers();          // (re)send current, microstep and StallGuard settings

}  // namespace sensors
