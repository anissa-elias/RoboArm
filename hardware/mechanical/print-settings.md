# Print settings

The files in [print/](print/) are laid flat for slicing, in millimetres. Regenerate them with `cad/prepare_print.py`. Everything fits a 256 x 256 x 260 mm bed. Nothing has been test-sliced or test-printed yet, so print the test parts first.

## Defaults

PETG, 0.4 mm nozzle, 0.2 mm layers, 4 walls, 40% infill, brim on anything tall or with a small base. Print toothed parts with 0.12 mm layers and 6 walls.

## Parts

| File | Qty | Supports | Notes |
|---|---|---|---|
| base_mount_plate | 1 | No | Nut pockets face the bed |
| base_shell | 1 | Light, for the wall openings | |
| base_deck | 1 | Under the encoder pad | |
| j1_motor_plate | 1 | No | Wait until the gearbox bolt pattern is measured |
| j1_rotor | 1 | Inside the bearing bore | Toothed |
| j1_bearing_cap | 1 | No | |
| j1_belt_cover | 1 | No | |
| j2_housing | 1 | Bearing seats | Wait until the gearbox is measured |
| j2_arm_root | 1 | Yes | Brim |
| j2_pulley | 1 | Lower flange | Toothed |
| j3_upper_arm | 1 | Yes, hump and head | Sits on its hump, so use a brim. Wait until the gearbox is measured |
| j3_arm_lid | 1 | No | Clips print upright |
| j3_elbow_stem | 1 | Yes | Brim |
| j3_elbow_pulley | 1 | Lower flange | Toothed |
| j4_forearm | 1 | Yes, hump and head | Brim. Wait until the motor is measured |
| j4_forearm_lid | 1 | Light | |
| j4_compound_pulley | 1 | Lower flange | Toothed |
| j4_wrist_pulley | 1 | Lower flange | Toothed |
| j4_wrist_link | 1 | Yes | Brim |
| j5_housing | 1 | Light | Wait until the motor is measured |
| j5_spindle | 1 | Lower flange | Toothed |
| j5_tool_flange | 1 | No | |
| gripper_body | 1 | Yes | Wait until the servo is measured |
| gripper_pinion | 1 | No | Toothed |
| gripper_rack | 2 | Yes | Toothed |
| gripper_finger | 2 | No | |

## Test first

1. A ring cut from `j1_rotor`, to tune the bearing press fit.
2. `j4_compound_pulley`, to check that GT2 teeth print cleanly with a real belt.
