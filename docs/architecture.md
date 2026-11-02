# Architecture

## Block diagram

```
                         +------------------+
                         |  Raspberry Pi 5  |  ROS 2 Jazzy: kinematics, planning, UI
                         +--------+---------+
                                  | USB (commands, telemetry; also powers the Mega)
                         +--------v---------+
                         | Arduino Mega 2560|  real-time step generation, sensor reading
                         +--+----+----+--+--+
        STEP/DIR/EN (x6)    |    |    |  |  PWM D9
              +-------------+    |    |  +-------------> gripper servo (6 V)
              v                  |    |
        +-----------+  UART x2   |    |  analog A0-A4
        | 5x TMC2209|<-----------+    +<------------ 5x AS5600 joint encoders
        +-----+-----+
              | 4 wires each
              v
        5x stepper motors
```

## Power

| Rail | Source | Feeds | Notes |
|---|---|---|---|
| 24 V motor bus | Bench supply (first tests, 3 A limit), later Mean Well LRS-200-24 | TMC2209 VM pins, gripper buck | 10 A fuse F0, then E-stop relay K1 |
| 6 V servo | XL4015 buck from the 24 V bus | MG996R gripper servo | 2 A fuse in, 3 A fuse out; set 6.0 V before connecting |
| 5 V logic | Mega 5 V pin (from Pi USB) | TMC2209 VDD, encoders, pull-ups | Logic only, never motor current |
| Pi 5 V | Official Pi 27 W USB-C supply | Raspberry Pi 5 | Separate from the motor supply |

All grounds are common. The 24 V bus never touches the Pi or the Mega.

## Arduino Mega pin map

| Function | Pins |
|---|---|
| STEP joint 1-5 | D22-D26 |
| DIR joint 1-5 | D30-D34 |
| EN joint 1-5 (LOW = driver on) | D36-D40, 10k pull-up holds drivers off during boot |
| Encoder angle joint 1-5 | A0-A4 (1k + 100 nF filter at the Mega) |
| TMC2209 UART bus A (joints 1-3) | Serial2: TX2 D16 (through 1k), RX2 D17 |
| TMC2209 UART bus B (joints 4-5) | Serial3: TX3 D14 (through 1k), RX3 D15 |
| Gripper servo PWM | D9 (through 1k) |
| Tool I2C (J6 plug) | SDA D20, SCL D21 |
| Spare | D0-D8, D10-D13, D18-D19, D27-D29, D35, D41-D53, A5-A15 |

## Design decisions

- **Absolute encoders instead of homing switches.** Each AS5600 reads a magnet on the joint output shaft (after any gearbox), so the arm knows every joint angle at power-up. This matches commercial arms and also catches skipped steps.
- **TMC2209 in UART mode.** MS1/MS2 set each driver's bus address (0-2); microstepping and current are set over UART. StallGuard gives a per-joint load reading for collision detection, plus over-temperature and open-wire flags.
- **E-stop drops a relay, not the motor current directly.** The button breaks the relay coil circuit, so pressing it or breaking its wire cuts the 24 V bus (fail-safe). The Pi and Mega stay powered.
- **No brakes.** Like the Niryo Ned2. The arm can sag when motor power is cut; support it during testing.
- **Centralized drivers.** Driver modules sit on one perfboard near the Mega. Per-joint smart modules on a CAN bus (as on commercial arms) are a possible later revision.

## Schematic

[hardware/electronics/output/roboarm_schematic.pdf](../hardware/electronics/output/roboarm_schematic.pdf), generated from [hardware/electronics/generate_schematic.py](../hardware/electronics/generate_schematic.py).
