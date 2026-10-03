# Firmware (Arduino Mega 2560)

`roboarm_mega/` is the motion-controller firmware. Pin map: [docs/architecture.md](../docs/architecture.md#arduino-mega-pin-map).

| File | Contents |
|---|---|
| `roboarm_mega.ino` | Serial protocol to the Pi, safety checks, gripper |
| `motion.cpp/.h` | Step generation (Timer2 ISR, 20 kHz) and per-joint trapezoidal velocity planning, all joints arrive together |
| `sensors.cpp/.h` | AS5600 encoder reading and zero offsets (EEPROM), TMC2209 UART setup and polling (load, over-temperature, open wire) |
| `config.h` | Pins, gear ratios, limits, currents, speeds. **Gear ratios and limits are placeholders until the mechanical design exists.** |

## Build

```bash
arduino-cli core install arduino:avr
arduino-cli lib install TMCStepper Servo
arduino-cli compile -b arduino:avr:mega firmware/roboarm_mega
# with nothing connected (fake encoders and drivers):
arduino-cli compile -b arduino:avr:mega --build-property build.extra_flags=-DRA_SIM=1 firmware/roboarm_mega
```

Or use the dev image, which has the toolchain: see [software/README.md](../software/README.md).

## Protocol (USB serial, 115200 baud, one command per line)

| Command | Meaning |
|---|---|
| `P` | Ping (keeps the 1 s link watchdog alive) |
| `E 1` / `E 0` | Enable / disable all drivers |
| `M a1 ... a6` | Move all joints to angles (degrees) |
| `J n a` | Move joint n to angle a |
| `X` | Stop smoothly |
| `V dps` / `A dps2` | Max joint speed / acceleration |
| `G a`, `G O`, `G C` | Gripper angle, open, close |
| `S` | Status line |
| `T hz` | Stream status (0 = off, max 50) |
| `Z` | Current pose becomes encoder zero (saved) |
| `R` | Re-sync step counters to encoders |
| `L n thr` | StallGuard threshold for joint n (0 = off) |
| `C` | Clear faults |

Status line: `S <faults> <enabled> <moving> | 6 commanded angles | 6 encoder angles | 6 loads | 6 driver flags`.
Fault bits: 1 link lost, 2 collision, 4 following error (> 5 deg between commanded and encoder), 8 no motor power (E-stop or 24 V off), 16 driver fault (open wire).

## Known limits (from the design review)

- The ATmega2560 tops out around 10 kHz steps per joint; with large gear reductions this limits joint speed. A faster motion MCU (Teensy 4.1 or a 6-driver STM32 board) is under consideration.
- TMC2209 registers reset when motor power drops; the firmware re-sends settings when a driver answers again, and stays disabled until faults are cleared.
- StallGuard only works while moving, in StealthChop; collision detection relies mainly on the encoder following error.
- TODO: E-stop input to the MCU, DIAG pin interrupts, encoder range/linearity calibration.
