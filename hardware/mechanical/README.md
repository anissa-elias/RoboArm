# Mechanical

RoboArm body the size of a Niryo Ned2: J1 base, J2 shoulder, J3 elbow, J4 wrist, J5 wrist twist, J6 gripper, with 491 mm reach and 300 g payload. Not yet CAD-frozen.

- [Mechanical design](../../docs/mechanical-design.md): joints, drivetrains, gripper and casing
- [cad/base_j1.py](cad/base_j1.py): base and J1 model. Generates the printable files in [stl/](stl/) and checks part fit.
- [joint_sizing.py](joint_sizing.py): torque, speed and belt-load calculations. Edit the masses as real parts are weighed and re-run.

## Planned layout

| Folder | Contents |
|---|---|
| `cad/` | Source CAD files |
| `stl/` | Printable parts |
| `print-settings.md` | Material, layer height, infill per part |
| `assembly.md` | Assembly guide |
