// RoboArm firmware for the Arduino Mega 2560.
//
// The Raspberry Pi sends plain-text commands over USB serial (115200 baud), one per line.
// Angles are joint degrees. Replies start with "OK", "ERR" or a status letter.
//
//   P                     ping (also keeps the link watchdog alive)
//   E 1 | E 0             enable / disable all motor drivers
//   M a1 a2 a3 a4 a5 a6   move all joints to these angles
//   J n a                 move joint n (1-6) to angle a
//   X                     stop smoothly
//   V dps | A dps2        set max joint speed / acceleration
//   G a                   gripper servo angle (or G O / G C for open / close)
//   S                     one status line
//   T hz                  stream status at hz (0 = off, max 50)
//   Z                     current pose becomes encoder zero (saved)
//   R                     re-sync step counters to the encoders
//   L n thr               StallGuard collision threshold for joint n (0 = off)
//   C                     clear faults
//   H                     help
//
// Status line:  S <fault> <en> <moving> | cmd: 6 angles | enc: 6 angles | load: 6 values | drv: 6 flags
// Build with RA_SIM=1 to run with nothing connected.

#include "config.h"
#include "motion.h"
#include "sensors.h"
#include <Servo.h>

enum Fault : uint8_t { F_NONE = 0, F_LINK = 1, F_COLLISION = 2, F_FOLLOW = 4, F_NO_MOTOR_POWER = 8, F_DRIVER = 16 };

static Servo gripper;
static bool enabled = false;
static uint8_t faults = F_NONE;
static uint32_t last_rx_ms = 0, last_stream_ms = 0;
static uint16_t stream_period_ms = 0;
static char line[96];
static uint8_t line_len = 0;

static void setEnabled(bool on) {
  if (on && faults) { Serial.println(F("ERR faults active, send C to clear")); return; }
  enabled = on;
  if (!on) motion::haltNow();
  for (uint8_t j = 0; j < NUM_JOINTS; j++) digitalWrite(PIN_EN[j], on ? LOW : HIGH);
}

static void raise(uint8_t f) {
  if (!(faults & f)) { faults |= f; Serial.print(F("FAULT ")); Serial.println(f); }
  motion::haltNow();
  setEnabled(false);
}

static void printStatus() {
  Serial.print(F("S ")); Serial.print(faults); Serial.print(' ');
  Serial.print(enabled ? 1 : 0); Serial.print(' ');
  Serial.print(motion::moving() ? 1 : 0); Serial.print(F(" |"));
  for (uint8_t j = 0; j < NUM_JOINTS; j++) { Serial.print(' '); Serial.print(motion::positionDeg(j), 2); }
  Serial.print(F(" |"));
  for (uint8_t j = 0; j < NUM_JOINTS; j++) { Serial.print(' '); Serial.print(sensors::encoderDeg(j), 2); }
  Serial.print(F(" |"));
  for (uint8_t j = 0; j < NUM_JOINTS; j++) { Serial.print(' '); Serial.print(sensors::load(j)); }
  Serial.print(F(" |"));
  for (uint8_t j = 0; j < NUM_JOINTS; j++) {
    uint8_t d = (sensors::driverOk(j) ? 1 : 0) | (sensors::overTemp(j) ? 2 : 0) | (sensors::openLoad(j) ? 4 : 0);
    Serial.print(' '); Serial.print(d);
  }
  Serial.println();
}

static void help() {
  Serial.println(F("RoboArm commands: P E M J X V A G S T Z R L C H (see roboarm_mega.ino header)"));
}

static void handle(char *s) {
  char cmd = toupper(s[0]);
  char *args = s + 1;
  switch (cmd) {
    case 'P': Serial.println(F("OK pong")); break;
    case 'E': setEnabled(atoi(args) != 0); if (!faults || !atoi(args)) Serial.println(F("OK")); break;
    case 'M': {
      float a[NUM_JOINTS]; char *p = args;
      for (uint8_t j = 0; j < NUM_JOINTS; j++) {
        char *end; a[j] = strtod(p, &end);
        if (end == p) { Serial.println(F("ERR need 6 angles")); return; }
        p = end;
      }
      if (!enabled) { Serial.println(F("ERR disabled, send E 1")); return; }
      motion::setTargets(a); Serial.println(F("OK"));
      break;
    }
    case 'J': {
      char *end; long n = strtol(args, &end, 10); float a = strtod(end, NULL);
      if (n < 1 || n > NUM_JOINTS) { Serial.println(F("ERR joint 1-6")); return; }
      if (!enabled) { Serial.println(F("ERR disabled, send E 1")); return; }
      motion::setTarget(n - 1, a); Serial.println(F("OK"));
      break;
    }
    case 'X': motion::stopAll(); Serial.println(F("OK")); break;
    case 'V': motion::setVmax(atof(args)); Serial.println(F("OK")); break;
    case 'A': motion::setAcc(atof(args)); Serial.println(F("OK")); break;
    case 'G': {
      while (*args == ' ') args++;
      int a = toupper(*args) == 'O' ? GRIPPER_OPEN_DEG : toupper(*args) == 'C' ? GRIPPER_CLOSED_DEG : atoi(args);
      gripper.write(constrain(a, 0, 180)); Serial.println(F("OK"));
      break;
    }
    case 'S': printStatus(); break;
    case 'T': { int hz = constrain(atoi(args), 0, 50); stream_period_ms = hz ? 1000 / hz : 0; Serial.println(F("OK")); break; }
    case 'Z':
      if (motion::moving()) { Serial.println(F("ERR moving")); return; }
      sensors::zeroEncoders();
      for (uint8_t j = 0; j < NUM_JOINTS; j++) motion::setPositionDeg(j, 0);
      Serial.println(F("OK zeroed"));
      break;
    case 'R':
      if (motion::moving()) { Serial.println(F("ERR moving")); return; }
      for (uint8_t j = 0; j < NUM_JOINTS; j++) motion::setPositionDeg(j, sensors::encoderDeg(j));
      Serial.println(F("OK"));
      break;
    case 'L': {
      char *end; long n = strtol(args, &end, 10); long thr = strtol(end, NULL, 10);
      if (n < 1 || n > NUM_JOINTS) { Serial.println(F("ERR joint 1-6")); return; }
      sensors::setSgThreshold(n - 1, (uint8_t)constrain(thr, 0, 255)); Serial.println(F("OK"));
      break;
    }
    case 'C': faults = F_NONE; Serial.println(F("OK cleared")); break;
    case 'H': help(); break;
    default: Serial.println(F("ERR unknown, H for help"));
  }
}

static void readHost() {
  while (Serial.available()) {
    char c = Serial.read();
    last_rx_ms = millis();
    if (c == '\r') continue;
    if (c == '\n') {
      line[line_len] = 0;
      if (line_len) handle(line);
      line_len = 0;
    } else if (line_len < sizeof(line) - 1) {
      line[line_len++] = c;
    }
  }
}

static void checkSafety() {
  if (!enabled) return;
  if (millis() - last_rx_ms > LINK_TIMEOUT_MS) raise(F_LINK);
  for (uint8_t j = 0; j < NUM_JOINTS; j++) {
    if (!sensors::driverOk(j)) { raise(F_NO_MOTOR_POWER); return; }   // E-stop pressed or 24 V off
    if (sensors::openLoad(j) && motion::moving()) { raise(F_DRIVER); return; }
    float err = fabs(motion::positionDeg(j) - sensors::encoderDeg(j));
    if (err > FOLLOW_ERROR_DEG) { raise(F_FOLLOW); return; }          // skipped steps or blocked joint
    uint8_t thr = sensors::sgThreshold(j);
    uint16_t ld = sensors::load(j);
    if (thr && motion::moving() && ld != 0xFFFF && ld < 2u * thr) { raise(F_COLLISION); return; }
  }
}

void setup() {
  for (uint8_t j = 0; j < NUM_JOINTS; j++) { pinMode(PIN_EN[j], OUTPUT); digitalWrite(PIN_EN[j], HIGH); }
  Serial.begin(HOST_BAUD);
  motion::begin();
  sensors::begin();
  // Encoders are absolute: start the step counters at the measured joint angles.
  for (uint8_t j = 0; j < NUM_JOINTS; j++) motion::setPositionDeg(j, sensors::encoderDeg(j));
  gripper.attach(PIN_GRIPPER);
  gripper.write(GRIPPER_OPEN_DEG);
  last_rx_ms = millis();
  Serial.print(F("RoboArm firmware ready"));
  Serial.println(RA_SIM ? F(" (SIM mode)") : F(""));
}

void loop() {
  readHost();
  motion::update();
  sensors::update();
  checkSafety();
  if (stream_period_ms && millis() - last_stream_ms >= stream_period_ms) {
    last_stream_ms = millis();
    printStatus();
  }
}
