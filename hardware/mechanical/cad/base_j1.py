"""Base and J1 turntable for RoboArm. All dimensions in mm, z = 0 on the table.

    pip install manifold3d trimesh numpy
    python base_j1.py

Writes printable STL files to ../stl/ and checks that the parts do not collide.
+X is the arm's front at J1 = 0. The rear wall is -X.

Measure before printing: anything marked CHECK came from a generic drawing, not the
actual part in hand.
"""
import math
from pathlib import Path

import numpy as np
import trimesh
from manifold3d import Manifold

SEG = 128
OUT = Path(__file__).resolve().parent.parent / 'stl'

# ---- base box
BASE = 200.0
WALL = 4.0
FLOOR = 4.0
DECK_TOP = 92.0
DECK_T = 6.0
DECK_BOT = DECK_TOP - DECK_T

# ---- bearings: 2 x 6813 (65 x 85 x 10)
B_ID, B_OD, B_W = 65.0, 85.0, 10.0
FIT = 0.15                 # radial clearance for a printed press fit; tune on a test ring
Z_COLLAR = DECK_TOP + 4.0  # lower inner race sits on the hub collar
Z_B1 = Z_COLLAR
Z_RIB = Z_B1 + B_W
RIB_H = 8.0
Z_B2 = Z_RIB + RIB_H
Z_B2_TOP = Z_B2 + B_W
HUB_BORE = 54.0

# ---- J1 belt: 20T on the gearbox shaft, 160T on the rotor, 400 mm 15 mm GT2 loop
TEETH_ROTOR, TEETH_MOTOR, BELT_PITCH, BELT_LEN = 160, 20, 2.0, 400.0
PD_ROTOR = TEETH_ROTOR * BELT_PITCH / math.pi
PD_MOTOR = TEETH_MOTOR * BELT_PITCH / math.pi
BELT_W = 15.0
Z_PULLEY = DECK_TOP + 5.0
PULLEY_H = BELT_W + 2.0


def belt_centre_distance():
    """Solve the open-belt length equation for the centre distance."""
    d, D = PD_MOTOR, PD_ROTOR
    lo, hi = 60.0, 140.0
    for _ in range(60):
        c = (lo + hi) / 2
        length = 2 * c + math.pi * (D + d) / 2 + (D - d) ** 2 / (4 * c)
        lo, hi = (c, hi) if length < BELT_LEN else (lo, c)
    return c


CENTRE = belt_centre_distance()
MOTOR_XY = (CENTRE * math.cos(math.pi / 4), CENTRE * math.sin(math.pi / 4))

# ---- motor, CHECK against the 17HS19-1684S-PG5 datasheet when it arrives
MOTOR_W, MOTOR_L, GBOX_D, GBOX_L = 42.3, 48.0, 36.0, 33.0
GBOX_BOSS_D, GBOX_PCD, GBOX_BOLT = 22.0, 28.0, 4.5
Z_GBOX_FACE = DECK_BOT + 1.0   # gearbox hangs from a boss that drops through the deck
PLATE_FLANGE = 3.0

# ---- rotor
ROTOR_R = 65.0
Z_PLATE = Z_B2_TOP + 5.0
PLATE_T = 6.0
Z_ROTOR_TOP = Z_PLATE + PLATE_T
J2_BOLT_SQ = 80.0

# ---- encoder: AS5600 module on a fixed centre post, magnet in the rotor
MAG_D, MAG_H = 6.2, 2.5
PAD = 24.0
Z_PAD_TOP = Z_PLATE - 4.2

STOP_R, STOP_ANGLE = 57.0, 225.0  # deck block opposite the motor

# Motor plate, long side along the belt. It slides +/- TENSION to set belt tension.
PLATE_L, PLATE_W, TENSION = 66.0, 44.0, 4.0
PLATE_SCREWS = [(sx, sy) for sx in (-28, 28) for sy in (-14, 14)]


def cyl(h, r, z=0.0, x=0.0, y=0.0, r2=None):
    m = Manifold.cylinder(h, r, r if r2 is None else r2, SEG)
    return m.translate((x, y, z))


def box(x0, x1, y0, y1, z0, z1):
    return Manifold.cube((x1 - x0, y1 - y0, z1 - z0)).translate((x0, y0, z0))


def merge(parts):
    return Manifold.compose(parts) if len(parts) > 1 else parts[0]


def rounded_square(size, r, h, z=0.0):
    a = size / 2 - r
    corners = [cyl(h, r, z, sx * a, sy * a) for sx in (-1, 1) for sy in (-1, 1)]
    return Manifold.batch_hull(corners)


# No corner post behind the motor: it would hit the motor body.
SCREW_XY = [(-86.0, -86.0), (-86.0, 86.0), (86.0, -86.0), (86.0, 40.0), (40.0, 86.0)]

# Pi 5 and Mega sit with their USB ends at the rear wall.
PI_HOLES = [(-8.5 - dx, 12 + 3.5 + dy) for dx in (0, 58) for dy in (0, 49)]
# CHECK the Mega holes against your board; clones can differ.
MEGA_HOLES = [(-90 + x, -62 + y) for x, y in
              ((13.97, 2.54), (15.24, 50.8), (66.04, 7.62), (66.04, 35.56), (90.17, 50.8), (96.52, 2.54))]
CARRIER_HOLES = [(sx, sy) for sx in (14, 84) for sy in (-16, -60)]  # CHECK against the board you cut


def base_shell():
    outer = rounded_square(BASE, 10, DECK_BOT)
    inner = rounded_square(BASE - 2 * WALL, 6, DECK_BOT, FLOOR)
    body = outer - inner

    posts = [cyl(DECK_BOT - FLOOR, 7, FLOOR, x, y) for x, y in SCREW_XY]
    stand = [cyl(6, 3.5, FLOOR, x, y) for x, y in PI_HOLES + MEGA_HOLES + CARRIER_HOLES]
    body = body + merge(posts) + merge(stand)

    cuts = [cyl(16, 2.1, DECK_BOT - 16, x, y) for x, y in SCREW_XY]                   # M4 inserts
    cuts += [cyl(9, 1.2, FLOOR + 1, x, y) for x, y in PI_HOLES + MEGA_HOLES + CARRIER_HOLES]
    cuts += [cyl(FLOOR + 2, 3.3, -1, x, y) for x, y in ((-85, 0), (85, 0), (0, 85), (0, -85))]  # M6 table bolts
    cuts.append(box(-BASE / 2 - 1, -BASE / 2 + WALL + 1, 14, 68, 12, 34))             # Pi ports
    cuts.append(box(-BASE / 2 - 1, -BASE / 2 + WALL + 1, -62, -18, 12, 30))           # Mega USB
    for y in (-8, 8):                                                                 # 24 V and E-stop cables
        cuts.append(cyl(WALL + 2, 6, 0).rotate((0, 90, 0)).translate((-BASE / 2 - 1, y, 60)))
    fan_axis = cyl(WALL + 2, 18.5, 0).rotate((90, 0, 0))
    cuts.append(fan_axis.translate((50, -BASE / 2 + WALL + 1, 44)))                   # 40 mm fan
    for sx in (-16, 16):
        for sz in (-16, 16):
            cuts.append(cyl(WALL + 2, 1.7, 0).rotate((90, 0, 0)).translate((50 + sx, -BASE / 2 + WALL + 1, 44 + sz)))
    for i in range(7):                                                                # exhaust slots
        y = -78 + i * 11
        cuts.append(box(BASE / 2 - WALL - 1, BASE / 2 + 1, y, y + 5, 20, 76))
    return body - merge(cuts)


def deck():
    plate = rounded_square(BASE, 10, DECK_T, DECK_BOT)
    collar = cyl(Z_COLLAR - DECK_TOP, 36, DECK_TOP)
    hub = cyl(Z_B2_TOP - 0.3 - DECK_TOP, (B_ID - FIT) / 2, DECK_TOP)
    block_x = STOP_R * math.cos(math.radians(STOP_ANGLE))
    block_y = STOP_R * math.sin(math.radians(STOP_ANGLE))
    stop = Manifold.cube((8, 10, Z_COLLAR - 0.5 - DECK_TOP), True).rotate((0, 0, STOP_ANGLE)) \
        .translate((block_x, block_y, DECK_TOP + (Z_COLLAR - 0.5 - DECK_TOP) / 2))
    body = plate + collar + hub + stop

    body -= cyl(Z_B2_TOP + 2, HUB_BORE / 2, DECK_BOT - 1)

    # Encoder post: two spokes, a centre post, and a pad for the AS5600 module.
    spokes = box(-HUB_BORE / 2 - 0.5, HUB_BORE / 2 + 0.5, -3, 3, DECK_BOT, DECK_TOP)
    post = cyl(Z_PAD_TOP - DECK_BOT - 3, 6, DECK_BOT)
    pad = box(-PAD / 2, PAD / 2, -PAD / 2, PAD / 2, Z_PAD_TOP - 3, Z_PAD_TOP)
    pad_holes = merge([cyl(5, 1.2, Z_PAD_TOP - 4.5, sx, sy) for sx in (-8.5, 8.5) for sy in (-8.5, 8.5)])
    body = body + spokes + post + (pad - pad_holes)

    cuts = [cyl(DECK_T + 2, 2.2, DECK_BOT - 1, x, y) for x, y in SCREW_XY]
    # Slot for the motor plate boss, plus clamp slots: the plate slides to tension the belt.
    a = math.pi / 4
    mx, my = MOTOR_XY
    ends = [(math.cos(a) * d, math.sin(a) * d) for d in (-TENSION, TENSION)]
    cuts.append(Manifold.batch_hull([cyl(DECK_T + 2, 21, DECK_BOT - 1, mx + ex, my + ey) for ex, ey in ends]))
    for lx, ly in PLATE_SCREWS:
        ox, oy = rotate_xy(lx, ly, 45)
        cuts.append(Manifold.batch_hull([cyl(DECK_T + 2, 2.2, DECK_BOT - 1, mx + ox + ex, my + oy + ey) for ex, ey in ends]))
    cuts += [cyl(5, 1.7, Z_B2_TOP - 5.3, r * math.cos(t), r * math.sin(t))
             for r, t in [(29.75, math.radians(x)) for x in (0, 120, 240)]]  # cap screws
    return body - merge(cuts)


def rotate_xy(x, y, deg):
    t = math.radians(deg)
    return x * math.cos(t) - y * math.sin(t), x * math.sin(t) + y * math.cos(t)


def motor_plate():
    """Clamps to the deck. Reprint if the gearbox bolt circle differs."""
    plate = box(-PLATE_L / 2, PLATE_L / 2, -PLATE_W / 2, PLATE_W / 2, DECK_TOP, DECK_TOP + PLATE_FLANGE)
    boss = cyl(DECK_TOP - Z_GBOX_FACE, 20, Z_GBOX_FACE)
    cuts = [cyl(12, GBOX_BOSS_D / 2 + 0.3, Z_GBOX_FACE - 1)]
    for i in range(4):
        x, y = rotate_xy(GBOX_PCD / 2, 0, 90 * i)
        cuts.append(cyl(12, GBOX_BOLT / 2, Z_GBOX_FACE - 1, x, y))
        cuts.append(cyl(3, 3.8, DECK_TOP + 0.5, x, y))
    for x, y in PLATE_SCREWS:
        cuts.append(cyl(12, 2.2, DECK_TOP - 1, x, y))
    return (plate + boss - merge(cuts)).rotate((0, 0, 45)).translate((MOTOR_XY[0], MOTOR_XY[1], 0))


def rotor():
    cup = cyl(Z_PLATE - Z_PULLEY, B_OD / 2 + 4.0, Z_PULLEY)
    pulley = cyl(PULLEY_H, PD_ROTOR / 2 - 0.25, Z_PULLEY)
    flange = cyl(1.5, PD_ROTOR / 2 + 1.5, Z_PULLEY + PULLEY_H)
    plate = cyl(PLATE_T, ROTOR_R, Z_PLATE)
    body = cup + pulley + flange + plate

    grooves = []
    for i in range(TEETH_ROTOR):
        t = 2 * math.pi * i / TEETH_ROTOR
        r = PD_ROTOR / 2 - 0.25
        grooves.append(Manifold.cylinder(PULLEY_H + 0.2, 0.6, 0.6, 16).translate((r * math.cos(t), r * math.sin(t), Z_PULLEY - 0.1)))
    body -= merge(grooves)

    # Bearing bores either side of the rib, then clearance for the cap and encoder.
    body -= cyl(B_W + (Z_B1 - Z_PULLEY) + 1, (B_OD + 2 * FIT) / 2, Z_PULLEY - 1)
    body -= cyl(RIB_H + 2, (B_OD - 6) / 2, Z_RIB - 1)
    body -= cyl(B_W, (B_OD + 2 * FIT) / 2, Z_B2)
    body -= cyl(Z_PLATE - Z_B2_TOP + 0.01, (B_OD - 6) / 2, Z_B2_TOP - 0.005)

    # Stop tab under the pulley, opposite the deck block at J1 = 0.
    tx, ty = STOP_R * math.cos(math.radians(45)), STOP_R * math.sin(math.radians(45))
    tab_h = Z_PULLEY - (DECK_TOP + 0.6)
    tab = Manifold.cube((8, 10, tab_h + 1), True).rotate((0, 0, 45)).translate((tx, ty, DECK_TOP + 0.6 + (tab_h + 1) / 2))
    body += tab

    # Magnet boss on the axis, cable slots around it, J2 mounting bolts.
    boss = cyl(Z_PLATE - (Z_PAD_TOP + 2.2), 6, Z_PAD_TOP + 2.2)
    body += boss
    slots = []
    for t in (0, 180):
        arc = [cyl(PLATE_T + 2, 6, Z_PLATE - 1, 26 * math.cos(math.radians(t + d)), 26 * math.sin(math.radians(t + d))) for d in (-35, 0, 35)]
        slots.append(Manifold.batch_hull(arc[:2]) + Manifold.batch_hull(arc[1:]))
    body -= merge(slots)
    body -= cyl(MAG_H, MAG_D / 2, Z_PAD_TOP + 2.2 - 0.01)
    q = J2_BOLT_SQ / 2
    body -= merge([cyl(PLATE_T + 1, 2.8, Z_PLATE + 0.5, sx * q, sy * q) for sx in (-1, 1) for sy in (-1, 1)])
    # Notch so the J2 pulley, which sits outside the fork, clears the plate.
    body -= box(-18, 18, 43.5, ROTOR_R + 1, Z_ROTOR_TOP - 3.5, Z_ROTOR_TOP + 1)
    return body


def bearing_cap():
    cap = cyl(4, 36, Z_B2_TOP) - cyl(6, HUB_BORE / 2, Z_B2_TOP - 1)
    screws = [cyl(6, 1.7, Z_B2_TOP - 1, 29.75 * math.cos(math.radians(a)), 29.75 * math.sin(math.radians(a))) for a in (0, 120, 240)]
    return cap - merge(screws)


def belt_cover():
    mx, my = MOTOR_XY
    outer = Manifold.batch_hull([cyl(28, 66, DECK_TOP), cyl(28, 25, DECK_TOP, mx, my)])
    inner = Manifold.batch_hull([cyl(26, 63, DECK_TOP - 1), cyl(26, 23, DECK_TOP - 1, mx, my)])
    # Notch so the cover sits over the motor plate at any tension setting.
    notch = box(-PLATE_L / 2 - TENSION - 1, PLATE_L / 2 + TENSION + 1, -PLATE_W / 2 - 1, PLATE_W / 2 + 1,
                DECK_TOP - 1, DECK_TOP + PLATE_FLANGE + 0.5).rotate((0, 0, 45)).translate((mx, my, 0))
    return outer - inner - notch - cyl(30, PD_ROTOR / 2 + 3, DECK_TOP)


def dummy_motor():
    mx, my = MOTOR_XY
    gbox = cyl(GBOX_L, GBOX_D / 2, Z_GBOX_FACE - GBOX_L, mx, my)
    z_motor = Z_GBOX_FACE - GBOX_L - MOTOR_L
    body = Manifold.cube((MOTOR_W, MOTOR_W, MOTOR_L), True).translate((mx, my, z_motor + MOTOR_L / 2))
    shaft = cyl(26, 4, Z_GBOX_FACE, mx, my)
    pulley = cyl(PULLEY_H, PD_MOTOR / 2, Z_PULLEY, mx, my)
    return gbox + body + shaft + pulley


def dummy_bearings():
    ring = lambda z: cyl(B_W, B_OD / 2, z) - cyl(B_W + 2, B_ID / 2, z - 1)
    return ring(Z_B1) + ring(Z_B2)


PRINTED = {
    'base_shell': base_shell,
    'base_deck': deck,
    'j1_motor_plate': motor_plate,
    'j1_rotor': rotor,
    'j1_bearing_cap': bearing_cap,
    'j1_belt_cover': belt_cover,
}


def to_trimesh(m):
    g = m.to_mesh()
    return trimesh.Trimesh(np.asarray(g.vert_properties)[:, :3], np.asarray(g.tri_verts), process=False)


def overlap(a, b):
    return (a ^ b).volume()


def checks(parts, motor, bearings):
    rot = parts['j1_rotor']
    pairs = [
        ('rotor', 'deck', rot, parts['base_deck']),
        ('rotor', 'cap', rot, parts['j1_bearing_cap']),
        ('rotor', 'belt cover', rot, parts['j1_belt_cover']),
        ('motor', 'rotor', motor, rot),
        ('motor', 'belt cover', motor, parts['j1_belt_cover']),
        ('deck', 'shell', parts['base_deck'], parts['base_shell']),
        ('motor', 'deck', motor, parts['base_deck']),
        ('plate', 'deck', parts['j1_motor_plate'], parts['base_deck']),
        ('plate', 'belt cover', parts['j1_motor_plate'], parts['j1_belt_cover']),
        ('deck post', 'motor', parts['base_shell'], motor),
    ]
    bad = 0
    for na, nb, a, b in pairs:
        v = overlap(a, b)
        print(f'  {na:12} vs {nb:12}: {v:8.2f} mm3 {"OK" if v < 1 else "COLLISION"}')
        bad += v >= 1
    print('  sweep J1 through its travel:')
    for name in ('base_deck', 'j1_belt_cover', 'j1_bearing_cap'):
        worst = max(overlap(rot.rotate((0, 0, a)), parts[name]) for a in range(-165, 166, 15))
        print(f'    rotor vs {name:15}: {worst:8.2f} mm3 {"OK" if worst < 1 else "COLLISION"}')
        bad += worst >= 1
    for a in (172, -172):
        v = overlap(rot.rotate((0, 0, a)), parts['base_deck'])
        print(f'    stop at {a:+d} deg engages: {v:.1f} mm3 {"OK" if v > 1 else "NO CONTACT"}')
        bad += v <= 1
    print(f'  belt centre distance {CENTRE:.2f} mm, motor at ({MOTOR_XY[0]:.1f}, {MOTOR_XY[1]:.1f})')
    print(f'  rotor pitch diameter {PD_ROTOR:.1f} mm, top of J1 at z = {Z_ROTOR_TOP:.1f}')
    return bad


def main():
    OUT.mkdir(exist_ok=True)
    parts = {name: fn() for name, fn in PRINTED.items()}
    motor, bearings = dummy_motor(), dummy_bearings()
    print('Parts:')
    for name, m in parts.items():
        lo, hi = m.bounding_box()[:3], m.bounding_box()[3:]
        size = [round(b - a, 1) for a, b in zip(lo, hi)]
        grams = m.volume() / 1000 * 1.27 * 0.6     # PETG, roughly 60% effective fill
        print(f'  {name:18} {size} mm, {m.num_vert()} verts, about {grams:.0f} g')
        tm = to_trimesh(m)
        assert tm.is_watertight, name
        tm.export(OUT / f'{name}.stl')
    print('Checks:')
    bad = checks(parts, motor, bearings)
    print('ALL CHECKS PASSED' if not bad else f'{bad} PROBLEMS')
    return parts, motor, bearings


if __name__ == '__main__':
    main()
