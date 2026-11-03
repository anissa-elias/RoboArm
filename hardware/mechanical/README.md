# Mechanical

RoboArm body the size of a Niryo Ned2: J1 base, J2 shoulder, J3 elbow, J4 wrist, J5 wrist twist, J6 gripper, with 504 mm reach and 300 g payload. Not yet CAD-frozen.

- [Mechanical design](../../docs/mechanical-design.md): joints, drivetrains, gripper and casing
- [cad/j2_shoulder.py](cad/j2_shoulder.py): J2 housing, arm root and 100T pulley.
- [print-settings.md](print-settings.md): print settings for every part. Slice the files in [print/](print/), which are already laid flat.
- [cad/j5_twist.py](cad/j5_twist.py): wrist housing, spindle and tool flange, with the gripper fitted.
- [cad/j4_forearm.py](cad/j4_forearm.py): slim forearm with wire tunnel, lid and clips, compound pulley, wrist pulley and wrist link.
- [cad/j3_elbow.py](cad/j3_elbow.py): slim upper arm with wire tunnel, lid and clips, elbow stem and 80T pulley.
- [cad/build_viewer.py](cad/build_viewer.py): builds the browser 3D model into `viewer/`.
- [cad/gripper.py](cad/gripper.py): two-jaw gripper and tool flange. Print 2 racks and 2 fingers.
- [cad/base_j1.py](cad/base_j1.py): base and J1 model. Generates the printable files in [stl/](stl/) and checks part fit.
- [joint_sizing.py](joint_sizing.py): torque, speed and belt-load calculations. Edit the masses as real parts are weighed and re-run.

## Planned layout

| Folder | Contents |
|---|---|
| `cad/` | Source CAD files |
| `stl/` | Printable parts |
| `print-settings.md` | Material, layer height, infill per part |
| `assembly.md` | Assembly guide |
