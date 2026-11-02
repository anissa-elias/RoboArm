// RoboArm firmware configuration (Arduino Mega 2560).
// Pin map matches hardware/electronics (see docs/architecture.md).
#pragma once
#include <Arduino.h>

// ---------------------------------------------------------------- build options
// RA_SIM 1: run with nothing connected. Encoders report the commanded position,
// TMC2209 UART is skipped, the driver-power check always passes.
#ifndef RA_SIM
#define RA_SIM 0
#endif

#define NUM_JOINTS 5
#define HOST_BAUD 115200      // USB serial to the Raspberry Pi
#define TMC_BAUD 115200       // TMC2209 single-wire UART

// ---------------------------------------------------------------- pins
// STEP D22-D26 = PORTA bits 0-4 (written directly in the step ISR)
// DIR  D30-D34, EN D36-D40 (LOW = driver enabled, 10k pull-ups hold them off at boot)
static const uint8_t PIN_DIR[NUM_JOINTS] = {30, 31, 32, 33, 34};
static const uint8_t PIN_EN[NUM_JOINTS]  = {36, 37, 38, 39, 40};
static const uint8_t PIN_ENC[NUM_JOINTS] = {A0, A1, A2, A3, A4};
static const uint8_t PIN_GRIPPER = 9;

// TMC2209 UART buses: joints 1-3 on Serial2, joints 4-5 on Serial3, addresses 0,1,2
static const uint8_t TMC_ADDR[NUM_JOINTS] = {0, 1, 2, 0, 1};

// ---------------------------------------------------------------- joints
// J1 base, J2 shoulder, J3 elbow, J4 wrist, J5 wrist twist. J6 is the tool on PIN_GRIPPER.
// Ratios and limits match docs/mechanical-design.md.
static const uint16_t MOTOR_STEPS = 200;   // 1.8 deg steppers
static const uint16_t MICROSTEPS = 8;
static const float GEAR_RATIO[NUM_JOINTS]   = {41.44, 68.65, 25.9, 15.0, 3.0};
static const int8_t   DIR_SIGN[NUM_JOINTS]  = {1, 1, 1, 1, 1};
static const int8_t   ENC_SIGN[NUM_JOINTS]  = {1, 1, 1, 1, 1};
static const float LIMIT_MIN[NUM_JOINTS]    = {-167, -35, -80, -110, -145};
static const float LIMIT_MAX[NUM_JOINTS]    = { 167,  90,  80,  110,  145};
// Motor RMS current (mA): 17HS19-1684S on J1-J3, 17HS08-1004S on J4, 11HS20-0674S on J5
static const uint16_t RMS_MA[NUM_JOINTS]    = {1400, 1400, 1400, 1000, 670};
static const float R_SENSE = 0.11f;        // BIGTREETECH TMC2209 V1.3 sense resistor

// ---------------------------------------------------------------- motion
static const uint32_t STEP_ISR_HZ = 20000;   // step timer rate; max 10 kHz steps per joint
static const float DEFAULT_VMAX_DPS = 30.0f; // joint speed, degrees per second
static const float DEFAULT_ACC_DPS2 = 60.0f; // joint acceleration, degrees per second^2
static const uint16_t CONTROL_HZ = 500;      // velocity planner rate

// ---------------------------------------------------------------- safety
static const uint16_t LINK_TIMEOUT_MS = 1000;   // no host message while enabled -> stop + disable
static const uint8_t  SG_THRESHOLD_DEFAULT = 0; // StallGuard collision threshold, 0 = off (tune per joint)
static const float    FOLLOW_ERROR_DEG = 5.0f;  // commanded vs encoder mismatch that raises a fault

// ---------------------------------------------------------------- gripper
static const uint8_t GRIPPER_OPEN_DEG = 20;
static const uint8_t GRIPPER_CLOSED_DEG = 110;
