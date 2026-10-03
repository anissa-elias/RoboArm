# Comparison with other arms

Checked October 2026. Specifications are from each project's own documentation.

| | RoboArm (planned) | Niryo Ned2 | Thor | PAROL6 | Faze4 |
|---|---|---|---|---|---|
| Joints | 6 + gripper | 6 + gripper | 6 + gripper | 6 + gripper | 6 + gripper |
| Onboard computer | Raspberry Pi 5, ROS 2 Jazzy | Raspberry Pi 4, ROS | None (PC) | None (PC) | None (PC) |
| Motion controller | Arduino Mega 2560 | Built in | Arduino Mega + Thor control PCB | STM32 board, TMC5160 | Teensy 3.5 |
| Joint position feedback | AS5600 absolute encoders | Magnetic encoders | None | Not listed | Limit switches |
| Collision detection | TMC2209 StallGuard | Yes | No | Not listed | No |
| E-stop | Yes (relay) | Not listed in specs | No | Not listed | No |
| Payload | TBD (body not designed) | 300 g | 750 g | 1 kg near base | Not listed |
| License | TBD | Commercial | CC-BY-SA 4.0 | GPL-3.0 | CERN-OHL-S 2.0 |
| Cost | Target below comparable open arms | Several thousand USD | Under 350 EUR | About 1,190 EUR partial kit | Under 1,000 USD |

Sources:
[Niryo Ned2 specifications](https://docs.niryo.com/robots/ned2/technical-specifications/) ·
[Thor](https://github.com/AngelLM/Thor) ·
[PAROL6 specifications](https://source-robotics.github.io/PAROL-docs/page2_2/) ·
[Faze4](https://github.com/Source-Robotics/Faze4-Robotic-arm)
