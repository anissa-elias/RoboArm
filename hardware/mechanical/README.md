# Mechanical

Not started. This folder will hold the 3D-printed body, CAD sources and print settings.

## To decide

- Body: adapt an existing open design or design a RoboArm body from scratch. If an existing design is adapted, follow its license and credit it.
- Joint layout and gear ratios for each of the 6 joints.
- Motor sizes per joint (the current BOM assumes 59 Ncm motors on joints 1-3 and short 16 Ncm motors on joints 4-6).
- Mounts for the AS5600 encoder magnets on each joint OUTPUT shaft, so the measured angle is the true joint angle.
- Cable routing through the joints.
- Mount for the driver carrier board, Mega, Pi 5 and E-stop in the base.

## Planned layout

| Folder | Contents |
|---|---|
| `cad/` | Source CAD files |
| `stl/` | Printable parts |
| `print-settings.md` | Material, layer height, infill per part |
| `assembly.md` | Assembly guide |
