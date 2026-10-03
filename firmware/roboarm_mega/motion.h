// Step generation (Timer1 ISR) and per-joint trapezoidal velocity planning.
#pragma once
#include "config.h"

namespace motion {

void begin();
void update();                       // call every loop; runs the planner at CONTROL_HZ
void setTarget(uint8_t j, float deg);
void setTargets(const float deg[NUM_JOINTS]);
void stopAll();                      // decelerate to a stop
void haltNow();                      // stop immediately (fault)
void setVmax(float dps);
void setAcc(float dps2);
float positionDeg(uint8_t j);        // commanded position, from step count
float targetDeg(uint8_t j);
bool moving();
void setPositionDeg(uint8_t j, float deg);  // re-sync step count (e.g. from encoder at boot)
float stepsPerDeg(uint8_t j);

}  // namespace motion
