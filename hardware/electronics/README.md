# Electronics

Single-sheet KiCad 9 schematic of the full RoboArm wiring. Every board pin is shown; parts are joined by drawn wires (red = 24 V bus, black = motor ground return, orange = 6 V servo rail).

| File | Purpose |
|---|---|
| `custom_arm.kicad_sch` | Schematic (open in KiCad 9) |
| `output/roboarm_schematic.pdf` | PDF export (A1) |
| `generate_schematic.py` | Generates the schematic from code |
| `verify_netlist.py` | Checks every intended connection in the exported netlist |
| `ArmModules.kicad_sym`, `sym-lib-table` | Custom symbols (Pi 5, Mega, TMC2209 module, AS5600 module, supplies, relay) |

## Regenerate and check

```bash
python generate_schematic.py
kicad-cli sch erc custom_arm.kicad_sch
kicad-cli sch export netlist -o output/arm.net custom_arm.kicad_sch
python verify_netlist.py output/arm.net
kicad-cli sch export pdf -o output/roboarm_schematic.pdf custom_arm.kicad_sch
```

Edit the generator, not the `.kicad_sch` file, so the two stay in sync.

## Before building

- TMC2209 module pin names differ between vendors; check the silkscreen.
- TMC2209 VM maximum is about 29 V: 24 V only.
- Set each driver's current and the buck module's 6.0 V output with a meter before connecting motors or the servo.
- Confirm the AS5600 modules run at 5 V.
