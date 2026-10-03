# Firmware (Arduino Mega 2560)

Not started. Pin map: [docs/architecture.md](../docs/architecture.md#arduino-mega-pin-map).

## Responsibilities

- Six-axis step generation with acceleration profiles (STEP D22-D27, DIR D30-D35)
- Driver enable control (EN D36-D41, LOW = on); disable all drivers on fault or lost link
- TMC2209 configuration over UART (Serial2 for joints 1-3, Serial3 for joints 4-6): current, microstepping, StealthChop, StallGuard thresholds
- Read joint angles from the AS5600 encoders (A0-A5) and compare with commanded position
- Collision detection from StallGuard load readings
- Gripper servo PWM (D9)
- Serial protocol to the Raspberry Pi (commands in, joint state and faults out)
