# Engineering calculations

Every number here comes from [joint_sizing.py](../hardware/mechanical/joint_sizing.py), unless noted. Run it to reproduce them. Masses, motor resistance and the usable-torque factor are estimates until real parts are weighed and measured.

## Degrees of freedom

Spatial mobility (Grubler): M = 6(n - 1) - 5j, for n links including the base and j revolute joints.

With 6 links and 5 joints, M = 6(5) - 25 = **5**.

| Freedom | Joints |
|---|---|
| Position of the wrist (3) | J1, J2, J3 |
| Tool pitch (1) | J4 |
| Tool twist (1) | J5 |
| Gripper open and close | J6, not counted because it does not move the tool in space |

A full pose needs 6. The missing one is tool yaw, so the tool always points in the arm's vertical plane.

## Mass

| Stage | Mass (kg) |
|---|---|
| Payload | 0.30 |
| Gripper | 0.20 |
| J5 motor and wrist | 0.30 |
| Forearm with J4 motor | 0.45 |
| Elbow | 0.30 |
| Upper arm | 0.45 |
| J3 motor and gearbox | 0.60 |
| **Total above J2** | **2.60** |

## Joint torque

Worst pose: arm stretched out level, with the payload 110 mm past the flange. Reach is 491 mm to the flange and 601 mm to the payload point.

Static torque comes from each mass times its horizontal distance from the joint, times 9.81. For J4:

T = 9.81 x (0.30 x 0.165 + 0.20 x 0.105 + 0.30 x 0.03) = 0.78 N·m

Design torque = 1.5 x static, to cover acceleration and friction.

Available torque = holding torque x (run current / rated current) x 0.6 usable x ratio x 0.85 efficiency. For J4:

0.16 x 1.0 x 0.6 x 15 x 0.85 = 1.22 N·m

| Joint | Static (N·m) | Design (N·m) | Ratio | Available (N·m) | Margin |
|---|---|---|---|---|---|
| J1 | 0.63 | 0.94 | 41.4 | 9.16 | 9.7 |
| J2, with 60% spring | 3.97 | 5.95 | 68.7 | 15.17 | 2.5 |
| J2, no spring | 7.27 | 10.90 | 68.7 | 15.17 | 1.4 |
| J3 | 2.92 | 4.38 | 25.9 | 5.72 | 1.3 |
| J4 | 0.78 | 1.17 | 15.0 | 1.22 | 1.05 |
| J5 | 0.06 | 0.09 | 3.0 | 0.18 | 2.1 |

J1 turns on a vertical axis, so gravity does not load it. Its torque comes from inertia: 0.29 kg·m² at 60°/s², plus 0.33 N·m of bearing friction (assumed).

The simulator agrees with J2: it measured 5.2 N·m holding the arm out with no payload and no spring. The simulator still uses the earlier 90 mm gripper length.

## Speed

Maximum speed = 10,000 steps/s / (200 x 8 x ratio) x 360.

| Joint | Max (°/s) | Ned2 (°/s) |
|---|---|---|
| J1 | 54 | 45 |
| J2 | 33 | 30 |
| J3 | 172 | 0.88 |
| J4 | 150 | 90 |
| J5 | 750 | 90 |

## Drive loads

| Joint | Belt tension (N) | Gearbox output (N·m) |
|---|---|---|
| J1 | 19 | 0.12 |
| J2, with spring | 187 | 1.19 |
| J2, no spring | 7.27 | 10.90 | 68.7 | 15.17 | 1.4 |
| J3 | 172 | 0.88 |

## Position resolution

| Joint | Degrees per microstep | Tip movement (mm) |
|---|---|---|
| J1 | 0.0054 | 0.047 |
| J2 | 0.0033 | 0.028 |
| J3 | 0.0087 | 0.041 |
| J4 | 0.0150 | 0.014 |
| J5 | 0.0750 | 0.039 |

This is commanded resolution, not accuracy. Backlash, belt stretch and flex will dominate. One count of the Mega's 10-bit ADC reading an AS5600 is 0.35°, about 3 mm at the tip.

## Base tipping

With the arm fully out, 2.60 kg sits 284 mm from the axis, which is 4.70 N·m about the base edge. A 1.9 kg base gives 1.86 N·m against it, a ratio of 0.40.

**The base tips over unless it is clamped or bolted down.** It is not safe to run free-standing. The mounting plate adds about 0.3 kg, which does not change this, so clamp the plate to the table.

## Power at 24 V

| Load | Estimate |
|---|---|
| Motor coil heat, all holding | 28 W, about 1.2 A |
| Mechanical work at J2 and J3 | 4 W |
| Servo stall (2.5 A at 6 V) | 15 W, about 0.7 A |
| **Design peak** | **about 2.6 A** |

A 24 V supply rated 5 A leaves a good margin. Coil resistances are typical values, not datasheet values.

## Not calculated yet

- Link deflection and stiffness of the printed parts, beyond a first estimate of about 1 mm at the elbow
- Bearing life and belt fatigue
- Vibration and resonance
- J2 spring rate, until the arm is weighed
