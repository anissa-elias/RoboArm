# RoboArm

An open, low-cost 6-axis robotic arm built entirely from commercial off-the-shelf (COTS) parts, designed for students to build, program and learn from.

RoboArm aims for the feature set of an educational desktop arm such as the Niryo Ned2 (onboard computer running ROS 2, joint encoders, collision detection, emergency stop) at a fraction of the cost, with every purchased part available on Amazon.

> Status: early design. The electronics schematic and bill of materials are complete and checked. The mechanical design, firmware and ROS 2 software are not started yet.

## Features (planned)

| Feature | How |
|---|---|
| 6 joints + gripper | NEMA 17 stepper motors, MG996R gripper servo |
| Onboard brain | Raspberry Pi 5 running ROS 2 Jazzy (Ubuntu 24.04) |
| Real-time motion | Arduino Mega 2560 generating step pulses |
| Quiet drivers | TMC2209 stepper drivers |
| Knows where it is at power-up | AS5600 absolute magnetic encoder on every joint output, no homing move |
| Collision and load sensing | TMC2209 StallGuard load readings over UART, per joint |
| Safety | Latching E-stop that drops a relay on the 24 V motor bus |
| Simple to source | Every purchased part on Amazon |

## How it works

```
Raspberry Pi 5 (ROS 2)  --USB-->  Arduino Mega 2560  --STEP/DIR/EN-->  6x TMC2209  -->  6x NEMA 17
                                       |  <--UART (load, temperature, open-wire)--  TMC2209
                                       |  <--analog angle--  6x AS5600 joint encoders
                                       +--PWM-->  gripper servo

24 V bench supply -> 10 A fuse -> E-stop relay -> 24 V bus -> drivers
                                                          -> 2 A fuse -> 6 V buck -> gripper servo
Pi 5 has its own USB-C supply and powers the Mega over USB.
```

Details: [docs/architecture.md](docs/architecture.md).

## Repository layout

| Folder | Contents |
|---|---|
| [hardware/electronics/](hardware/electronics/) | KiCad schematic (every pin shown), generator script, connection checker, PDF |
| [hardware/bom/](hardware/bom/) | Bill of materials with Amazon links |
| [hardware/mechanical/](hardware/mechanical/) | 3D-printed body, CAD, print settings (open) |
| [firmware/](firmware/) | Arduino Mega firmware (open) |
| [software/](software/) | ROS 2 packages, simulation, tools (open) |
| [docs/](docs/) | Architecture, design decisions, roadmap |

## Cost

Electronics and motors: about **$268** before tax and shipping (estimate, see [hardware/bom/](hardware/bom/)). This excludes the Raspberry Pi 5, its power supply, the Arduino Mega, a 24 V bench supply, printed parts and mechanical hardware. Target: a complete arm cheaper than comparable open-source arms.

## Roadmap

See [docs/roadmap.md](docs/roadmap.md).

## Related open-source arms

RoboArm learns from existing open designs, including [Thor](https://github.com/AngelLM/Thor), [PAROL6](https://github.com/Source-Robotics/PAROL6-Desktop-robot-arm), [Faze4](https://github.com/Source-Robotics/Faze4-Robotic-arm), [SmallRobotArm](https://github.com/SkyentificGit/SmallRobotArm) and the [AR4](https://www.anninrobotics.com). See [docs/comparison.md](docs/comparison.md).

## Safety

This is an experimental machine. Motors can move suddenly and pinch. Keep the E-stop within reach, set a current limit on the supply during first tests, and never plug or unplug a motor with power applied.

## License

To be decided.
