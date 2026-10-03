#include "sensors.h"
#include "motion.h"
#include <EEPROM.h>
#include <TMCStepper.h>

namespace sensors {

static TMC2209Stepper drv[NUM_JOINTS] = {
  TMC2209Stepper(&Serial2, R_SENSE, TMC_ADDR[0]),
  TMC2209Stepper(&Serial2, R_SENSE, TMC_ADDR[1]),
  TMC2209Stepper(&Serial2, R_SENSE, TMC_ADDR[2]),
  TMC2209Stepper(&Serial3, R_SENSE, TMC_ADDR[3]),
  TMC2209Stepper(&Serial3, R_SENSE, TMC_ADDR[4]),
  TMC2209Stepper(&Serial3, R_SENSE, TMC_ADDR[5]),
};

static float enc_offset[NUM_JOINTS];
static float enc_deg[NUM_JOINTS];
static bool ok[NUM_JOINTS];
static uint16_t sg[NUM_JOINTS];
static bool ot[NUM_JOINTS], ol[NUM_JOINTS];
static uint8_t sg_thr[NUM_JOINTS];
static uint8_t poll_idx = 0;
static uint32_t last_enc_ms = 0, last_poll_ms = 0;

static const int EE_MAGIC = 0, EE_OFFSETS = 4;
static const uint32_t MAGIC = 0x52414131UL;  // "RAA1"

static float wrap180(float a) {
  while (a > 180.0f) a -= 360.0f;
  while (a < -180.0f) a += 360.0f;
  return a;
}

static float rawDeg(uint8_t j) {
  // AS5600 analog output: 0..VCC maps to 0..360 degrees; Mega ADC is 10-bit.
  return analogRead(PIN_ENC[j]) * (360.0f / 1024.0f);
}

void configureDrivers() {
#if !RA_SIM
  for (uint8_t j = 0; j < NUM_JOINTS; j++) {
    TMC2209Stepper &d = drv[j];
    d.begin();
    d.pdn_disable(true);        // PDN_UART pin is the UART, not power-down
    d.mstep_reg_select(true);   // microsteps from register, MS1/MS2 are the address
    d.I_scale_analog(false);
    d.toff(4);
    d.blank_time(24);
    d.rms_current(RMS_MA[j]);
    d.microsteps(MICROSTEPS);
    d.en_spreadCycle(false);    // StealthChop: quiet, and required for StallGuard4
    d.pwm_autoscale(true);
    d.TCOOLTHRS(0xFFFFF);       // StallGuard active at all speeds above standstill
    d.SGTHRS(sg_thr[j]);
    ok[j] = d.test_connection() == 0;
  }
#else
  for (uint8_t j = 0; j < NUM_JOINTS; j++) ok[j] = true;
#endif
}

void begin() {
  Serial2.begin(TMC_BAUD);
  Serial3.begin(TMC_BAUD);
  uint32_t m;
  EEPROM.get(EE_MAGIC, m);
  for (uint8_t j = 0; j < NUM_JOINTS; j++) {
    if (m == MAGIC) EEPROM.get(EE_OFFSETS + j * sizeof(float), enc_offset[j]);
    else enc_offset[j] = 0;
    sg[j] = 0xFFFF; sg_thr[j] = SG_THRESHOLD_DEFAULT; ot[j] = ol[j] = false;
  }
  configureDrivers();
  for (uint8_t j = 0; j < NUM_JOINTS; j++) {
#if RA_SIM
    enc_deg[j] = 0;
#else
    enc_deg[j] = wrap180(ENC_SIGN[j] * rawDeg(j) - enc_offset[j]);
#endif
  }
}

void update() {
  uint32_t now = millis();
  if (now - last_enc_ms >= 10) {        // 100 Hz encoder sampling
    last_enc_ms = now;
    for (uint8_t j = 0; j < NUM_JOINTS; j++) {
#if RA_SIM
      enc_deg[j] = motion::positionDeg(j);
#else
      float a = wrap180(ENC_SIGN[j] * rawDeg(j) - enc_offset[j]);
      enc_deg[j] = 0.7f * enc_deg[j] + 0.3f * a;   // light smoothing
#endif
    }
  }
#if !RA_SIM
  if (now - last_poll_ms >= 20) {       // one driver per 20 ms: each joint every 120 ms
    last_poll_ms = now;
    TMC2209Stepper &d = drv[poll_idx];
    bool was_ok = ok[poll_idx];
    ok[poll_idx] = d.test_connection() == 0;
    if (ok[poll_idx]) {
      if (!was_ok) configureDrivers();  // motor power came back: re-send settings
      sg[poll_idx] = d.SG_RESULT();
      uint32_t st = d.DRV_STATUS();
      ot[poll_idx] = st & (1UL << 1);           // otpw: over-temperature pre-warning
      ol[poll_idx] = st & ((1UL << 6) | (1UL << 7));  // ola/olb: open load
    } else {
      sg[poll_idx] = 0xFFFF;
    }
    poll_idx = (poll_idx + 1) % NUM_JOINTS;
  }
#endif
}

float encoderDeg(uint8_t j) { return enc_deg[j]; }

void zeroEncoders() {
  for (uint8_t j = 0; j < NUM_JOINTS; j++) {
#if RA_SIM
    enc_offset[j] = 0;
#else
    enc_offset[j] = ENC_SIGN[j] * rawDeg(j);
#endif
    EEPROM.put(EE_OFFSETS + j * sizeof(float), enc_offset[j]);
    enc_deg[j] = 0;
  }
  EEPROM.put(EE_MAGIC, MAGIC);
}

bool driverOk(uint8_t j) { return ok[j]; }
uint16_t load(uint8_t j) { return sg[j]; }
bool overTemp(uint8_t j) { return ot[j]; }
bool openLoad(uint8_t j) { return ol[j]; }
void setSgThreshold(uint8_t j, uint8_t thr) {
  sg_thr[j] = thr;
#if !RA_SIM
  drv[j].SGTHRS(thr);
#endif
}
uint8_t sgThreshold(uint8_t j) { return sg_thr[j]; }

}  // namespace sensors
