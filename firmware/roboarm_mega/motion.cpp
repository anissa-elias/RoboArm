#include "motion.h"
#include <util/atomic.h>

namespace motion {

// Shared with the ISR. vel_q16: steps per ISR tick in 16.16 fixed point, signed.
static volatile int32_t pos_steps[NUM_JOINTS];
static volatile int32_t vel_q16[NUM_JOINTS];
static uint32_t acc_q16[NUM_JOINTS];      // ISR-only phase accumulators

static int32_t target_steps[NUM_JOINTS];
static float vel_sps[NUM_JOINTS];         // planner velocity, steps per second (signed)
static float vmax_dps = DEFAULT_VMAX_DPS;
static float acc_dps2 = DEFAULT_ACC_DPS2;
static float spd[NUM_JOINTS];             // steps per degree
static float axis_vmax[NUM_JOINTS];       // per-axis speed so all joints arrive together
static float axis_acc[NUM_JOINTS];
static uint32_t last_us = 0;
static bool halted = false;

float stepsPerDeg(uint8_t j) { return spd[j]; }

static void syncAxes() {
  // Scale each joint's speed by its share of the longest move so they finish together.
  float dist[NUM_JOINTS], longest = 0;
  for (uint8_t j = 0; j < NUM_JOINTS; j++) {
    int32_t p;
    ATOMIC_BLOCK(ATOMIC_RESTORESTATE) { p = pos_steps[j]; }
    dist[j] = fabs((float)(target_steps[j] - p)) / spd[j];
    if (dist[j] > longest) longest = dist[j];
  }
  for (uint8_t j = 0; j < NUM_JOINTS; j++) {
    float share = longest > 0 ? dist[j] / longest : 1.0f;
    if (share < 0.05f) share = 0.05f;
    axis_vmax[j] = vmax_dps * share * spd[j];
    axis_acc[j] = acc_dps2 * share * spd[j];
  }
}

void begin() {
  for (uint8_t j = 0; j < NUM_JOINTS; j++) {
    spd[j] = (float)MOTOR_STEPS * MICROSTEPS * GEAR_RATIO[j] / 360.0f;
    pos_steps[j] = 0; vel_q16[j] = 0; acc_q16[j] = 0; target_steps[j] = 0; vel_sps[j] = 0;
    pinMode(PIN_DIR[j], OUTPUT);
  }
  DDRA |= 0x3F;   // STEP pins D22-D27
  PORTA &= ~0x3F;
  syncAxes();
  // Timer2 (Timers 1/3/4/5 belong to the Servo library on the Mega), CTC mode, prescaler 8:
  // 16 MHz / 8 / (OCR2A + 1) = STEP_ISR_HZ
  cli();
  TCCR2A = (1 << WGM21); TCCR2B = (1 << CS21); TCNT2 = 0;
  OCR2A = (F_CPU / 8 / STEP_ISR_HZ) - 1;
  TIMSK2 |= (1 << OCIE2A);
  sei();
  last_us = micros();
}

ISR(TIMER2_COMPA_vect) {
  PORTA &= ~0x3F;                 // end previous step pulses (>= 50 us wide)
  uint8_t out = 0;
  for (uint8_t j = 0; j < NUM_JOINTS; j++) {
    int32_t v = vel_q16[j];
    if (v == 0) continue;
    uint32_t mag = v > 0 ? (uint32_t)v : (uint32_t)(-v);
    acc_q16[j] += mag;
    if (acc_q16[j] >= 65536UL) {
      acc_q16[j] -= 65536UL;
      out |= (1 << j);
      pos_steps[j] += (v > 0) ? 1 : -1;
    }
  }
  PORTA |= out;
}

static void setDir(uint8_t j, float v) {
  bool fwd = (v >= 0) == (DIR_SIGN[j] > 0);
  digitalWrite(PIN_DIR[j], fwd ? HIGH : LOW);
}

void update() {
  uint32_t now = micros();
  float dt = (now - last_us) * 1e-6f;
  if (dt < 1.0f / CONTROL_HZ) return;
  last_us = now;
  if (dt > 0.05f) dt = 0.05f;
  for (uint8_t j = 0; j < NUM_JOINTS; j++) {
    int32_t p;
    ATOMIC_BLOCK(ATOMIC_RESTORESTATE) { p = pos_steps[j]; }
    float rem = (float)(target_steps[j] - p);
    float dir = rem > 0 ? 1.0f : (rem < 0 ? -1.0f : 0.0f);
    // fastest speed that still lets us stop at the target: v = sqrt(2 a d)
    float vstop = sqrtf(2.0f * axis_acc[j] * fabs(rem));
    float vdes = dir * min(axis_vmax[j], vstop);
    if (halted || fabs(rem) < 1.0f) vdes = 0;
    float dv = axis_acc[j] * dt;
    float v = vel_sps[j];
    if (vdes > v) v = min(v + dv, vdes); else v = max(v - dv, vdes);
    vel_sps[j] = v;
    // never exceed the ISR's 1-step-per-2-ticks limit
    float vmax_isr = STEP_ISR_HZ / 2.0f;
    if (v > vmax_isr) v = vmax_isr; else if (v < -vmax_isr) v = -vmax_isr;
    if (v != 0) setDir(j, v);
    int32_t q = (int32_t)(v / STEP_ISR_HZ * 65536.0f);
    ATOMIC_BLOCK(ATOMIC_RESTORESTATE) { vel_q16[j] = q; }
  }
}

static int32_t degToSteps(uint8_t j, float deg) {
  if (deg < LIMIT_MIN[j]) deg = LIMIT_MIN[j];
  if (deg > LIMIT_MAX[j]) deg = LIMIT_MAX[j];
  return (int32_t)lroundf(deg * spd[j]);
}

void setTarget(uint8_t j, float deg) { halted = false; target_steps[j] = degToSteps(j, deg); syncAxes(); }

void setTargets(const float deg[NUM_JOINTS]) {
  halted = false;
  for (uint8_t j = 0; j < NUM_JOINTS; j++) target_steps[j] = degToSteps(j, deg[j]);
  syncAxes();
}

void stopAll() {
  // new target = where we would stop from the current speed
  for (uint8_t j = 0; j < NUM_JOINTS; j++) {
    int32_t p;
    ATOMIC_BLOCK(ATOMIC_RESTORESTATE) { p = pos_steps[j]; }
    float v = vel_sps[j];
    float a = axis_acc[j] > 0 ? axis_acc[j] : 1.0f;
    float d = v * fabs(v) / (2.0f * a);
    target_steps[j] = p + (int32_t)d;
  }
}

void haltNow() {
  halted = true;
  for (uint8_t j = 0; j < NUM_JOINTS; j++) {
    vel_sps[j] = 0;
    ATOMIC_BLOCK(ATOMIC_RESTORESTATE) { vel_q16[j] = 0; target_steps[j] = pos_steps[j]; }
  }
}

void setVmax(float dps) { if (dps > 0) { vmax_dps = dps; syncAxes(); } }
void setAcc(float dps2) { if (dps2 > 0) { acc_dps2 = dps2; syncAxes(); } }

float positionDeg(uint8_t j) {
  int32_t p;
  ATOMIC_BLOCK(ATOMIC_RESTORESTATE) { p = pos_steps[j]; }
  return p / spd[j];
}
float targetDeg(uint8_t j) { return target_steps[j] / spd[j]; }

bool moving() {
  for (uint8_t j = 0; j < NUM_JOINTS; j++) {
    int32_t p;
    ATOMIC_BLOCK(ATOMIC_RESTORESTATE) { p = pos_steps[j]; }
    if (p != target_steps[j] || vel_sps[j] != 0) return true;
  }
  return false;
}

void setPositionDeg(uint8_t j, float deg) {
  int32_t s = (int32_t)lroundf(deg * spd[j]);
  ATOMIC_BLOCK(ATOMIC_RESTORESTATE) { pos_steps[j] = s; }
  target_steps[j] = s;
  vel_sps[j] = 0;
}

}  // namespace motion
