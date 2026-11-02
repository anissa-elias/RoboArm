# Mechanical design

Status: chosen joint layout. The base, J1 and gripper are modeled in [hardware/mechanical/cad](../hardware/mechanical/cad); J2-J5 are not yet. Full working is in [engineering-calculations.md](engineering-calculations.md), from [joint_sizing.py](../hardware/mechanical/joint_sizing.py). Masses in it are estimates, so re-run it as parts are weighed.

## Size target

| | Niryo Ned2 | RoboArm target |
|---|---|---|
| Reach | 490 mm | 491 mm from the shoulder to the flange |
| Payload | 300 g at 20 mm | 300 g, sized at 110 mm past the flange to include the gripper |
| Weight | 7 kg | About 5-6 kg (estimate) |
| Footprint | 181.6 x 187.5 mm | 200 x 200 mm |
| Repeatability | ±0.5 mm | Not promised; about ±1-3 mm expected until measured |

Ned2 figures are from Niryo's [spec sheet](https://niryo.com/wp-content/uploads/2026/06/10001874-4_TECHNICAL_SPECIFICATIONS_NED2.pdf) and geometry from its [public URDF](https://github.com/NiryoRobotics/ned_ros/blob/master/niryo_robot_description/urdf/ned2/niryo_ned2.urdf.xacro).

| Dimension | RoboArm |
|---|---|
| Table to J2 axis | 166 mm |
| J2 to J3 (upper arm) | 221 mm |
| J3 to J4 (forearm) | 215 mm |
| J4 to flange (wrist) | 55 mm |

## Joints

| Joint | Motion | Axis | Range | Motor | Reduction | Design torque | Available | Margin | Max speed |
|---|---|---|---|---|---|---|---|---|---|
| J1 | Base rotation | Z, vertical | 335° | 17HS19-1684S-PG5 | 5.18 x 8 = 41.4:1 | 0.9 N·m | 9.2 | 9.7 | 54°/s |
| J2 | Shoulder | Y, sideways | 125° | 17HS19-1684S-PG14 | 13.73 x 5 = 68.7:1 | 5.7 N·m with spring | 15.2 | 2.6 (1.5 without) | 33°/s |
| J3 | Elbow | Y, sideways | 160° | 17HS19-1684S-PG5 | 5.18 x 5 = 25.9:1 | 4.3 N·m | 5.7 | 1.3 | 87°/s |
| J4 | Wrist | Y, sideways | 220° | 17HS08-1004S at 1.0 A | Belts 3 x 5 = 15:1 | 1.17 N·m | 1.22 | 1.05 | 150°/s |
| J5 | Wrist twist | X, along the hand | 290° | 11HS20-0674S | Belt 3:1 | 0.09 N·m | 0.18 | 2.1 | 750°/s |
| J6 | Gripper | Open and close | 0-50 mm | MG996R servo | Rack and pinion | - | - | - | - |

Assumptions: usable motor torque is 60% of holding torque, drivetrain efficiency is 85%, and design torque is 1.5 x the static load. The speed limit comes from 8 microsteps and the firmware's 10 kHz step ceiling.

J1 and J2 are two stacked hinges rather than a ball joint: J1 aims the arm left and right, and J2 aims it up and down. Ranges are limited by hard stops so cables can run through the joints without slip rings.

### Layout along the arm

- **J1:** the motor hangs from the deck inside the base, with a 20T pulley driving a 160T pulley printed on the turntable by a 400 mm, 15 mm belt. Two 6813 bearings on a fixed hub carry the turntable. The pulley has to surround the bearings, which is why it is 160T. See [the CAD](../hardware/mechanical/cad/base_j1.py).
- **J2:** the motor is on the turntable and drives a 100T printed pulley on the shoulder axle, on 6806 bearings. An extension spring from the turntable to the upper arm carries about 60% of the arm's own weight, and also slows the drop when the E-stop cuts power.
- **J3:** the motor sits at the shoulder end of the upper arm, with its gearbox driving the elbow by a 15 mm belt, on 6804 bearings. A gear-only elbow would put the motor at the elbow, adding about 0.6 kg for J2 to lift, and printed gear backlash of about 0.5° would move the tip about 4 mm.
- **J4:** the motor rides at the rear of the forearm, with a 6 mm belt down to the wrist axle on 6802 bearings.
- **J5:** the NEMA 11 rides in the wrist beside the twist axis and drives the flange by a short belt, on 6803 bearings. This avoids mechanical coupling with J4.
- **J6:** the MG996R sits in the gripper.

### Encoders

Each AS5600 needs a magnet on the joint's rotation axis.

- **J2, J3, J4, J5:** the magnet goes on the axle end, with the module fixed facing it.
- **J1:** the module sits on a fixed post in the centre of the hub, with the magnet in the turntable above it. Cables wrap around the post through the 54 mm bore. A 1:1 belt to a side sensor would need a second 160T pulley, which does not fit.

The Mega's 10-bit ADC limits the absolute reading to 0.35°, or about 3 mm at the tip. Encoders handle start-up position and fault detection, while step counting gives the fine position.

### Cable routing

J2 is the busiest crossing: motors J3-J5, encoders J3-J5, and the servo, about 27 conductors. Use thin silicone wire in loose loops with strain relief on both sides of each joint, and hard stops to prevent over-rotation. Stock motor leads are 1 m, so J4 and J5 need extending at a connector in the turntable.

## Gripper (J6)

A parallel two-jaw gripper, driven by the MG996R through a rack and pinion.

| Item | Decision |
|---|---|
| Stroke | 0-50 mm opening |
| Mechanism | 21 mm pitch-diameter pinion (module 1.5, 14 teeth) on the servo, two opposed racks on two 4 mm rods. 110 mm wide, 130 mm long |
| Grip force | Up to about 50 N from the servo's claimed stall torque. Limit by commanded position and use soft jaws |
| Pads | TPU or rubber on replaceable screw-on fingers |
| Mass | Under 200 g including the servo |

The servo cannot report force and heats up if it stalls on an object, so firmware should back off after closing.

## Modular tools

J6 is a swappable tool, not a fixed gripper. Every tool uses the same mount and plug, and is changed by hand with a few screws. Everything past the J5 flange belongs to the tool.

| Item | Standard |
|---|---|
| Mount | 4 M3 bolts on a printed flange, with a locating pin so tools only fit one way |
| Plug | 6-pin GX12 connector on the wrist |
| Pins | 6 V, GND, servo PWM, 5 V, I2C SDA, I2C SCL (Mega D20, D21) |
| Air | 4 mm OD silicone tube routed from the base to the wrist, capped when unused |
| Tool power | 6 V up to 3 A from the servo rail. 5 V is logic only |
| Weight limit | Tool plus payload under 500 g at 110 mm from the flange |

| Tool | How it connects | Limit |
|---|---|---|
| Two-jaw gripper | One servo on the PWM pin | Standard tool |
| 4-finger gripper, one servo | All fingers linked to one servo on the PWM pin | Heavier tool leaves less payload |
| 4-finger gripper, separate fingers | Small servos on a PCA9685 board in the tool, over I2C | 3 A shared across all servos, so MG996R-size servos are too large. Test I2C over the arm-length cable |
| Vacuum | Pump and valve in the base, air through the tube, cup on the tool | Pump and valve need their own driver and a 24 V or 12 V supply, added when a vacuum tool is built |
| Pen holder or fixed fingers | Mount only | - |

The air tube passes J1, J2, J3 and J4 alongside the wires, and needs a rotary fitting or a slack loop at J5. Firmware needs a setting for which tool is fitted.

## Casing

The casing is the structure: printed PETG clamshells, stiffened with metal where bending loads are highest.

| Section | Construction |
|---|---|
| Base | 200 x 200 mm printed box holding Pi, Mega, driver carrier, buck module and J1 motor. Rear panel for connectors, side vents, fan airflow across the drivers, E-stop on a tethered box |
| Turntable | Thick printed housing on the J1 bearings, carrying the J2 motor and spring anchor |
| Upper arm | Clamshell around two 2020 extrusions, about 70 mm wide |
| Forearm | Clamshell around two 10 mm aluminium rods, tapering to a fork at J4 |
| Wrist | Printed housing for the NEMA 11 |

- Print load-bearing parts with 4+ walls and 40% infill, with layers running along the load path.
- Use heat-set inserts wherever screws will be removed more than once.
- Keep belts covered: they are pinch points.
- The 24 V supply stays outside the base, so there is no mains voltage inside the arm.
- The arm must be clamped or bolted to the table. The base is too light to resist tipping at full reach.

## Risks

| Risk | Plan |
|---|---|
| J4 margin is only 1.05 at its full rated 1 A | Measure it early. Fallback: shorten the gripper, lighten the wrist, or use a higher belt ratio |
| PG14 gearbox limit not confirmed | The design puts 2.1 N·m on it with no spring. Check the datasheet before buying; 3 N·m is an unconfirmed figure from a related listing |
| J2 belt load is about 180 N with the spring, 320 N without | Test a 15 mm belt and printed pulley under load first. If teeth skip, use a larger pulley or a stronger belt |
| No brakes | Reduced by the J2 spring, but the arm can still fall. Support it during testing |
| Elbow and shoulder stiffness | Measure deflection on a test section before printing the full arm |

## Follow-up changes

- URDF: use the axes and lengths in this document.
- J2 housing: J1 tops out at 135 mm, 31 mm below the J2 axis, and the J2 pulley radius is 32 mm. Offset the pulley to one side or pocket it into the turntable.
