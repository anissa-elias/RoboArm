"""J4 wrist hinge and slim forearm for RoboArm. All dimensions in mm, same frame as base_j1.py.

    pip install manifold3d trimesh numpy
    python j4_forearm.py

The forearm is drawn at J3 = 0, pointing along +X from the elbow. The wrist axis runs along Y.
A rib splits the tunnel into wires (-Y) and belts (+Y). The lid is on the underside.
Writes STL files to ../stl/ and checks fit through the J3 and J4 travel.
Measure before printing: anything marked CHECK came from a generic drawing.
"""
import math

from manifold3d import Manifold

from base_j1 import OUT, box, cyl, to_trimesh
from j2_shoulder import ycyl
from j3_elbow import (Z_E, HEAD_Y, RIB_Y, bend, clip_profile, dummy_j3_motor, elbow_pulley, elbow_stem, lid as arm_lid,
                      upper_arm)

WALL = 3.0
X_ROOT = 60.0                 # front of the elbow stem
STEM_Y = (-HEAD_Y + 9.6, RIB_Y[1] - 0.4)
STEM_C = sum(STEM_Y) / 2
X_W = 215.0                   # wrist axis
HALF_Y, HALF_Z = 24.0, 23.0   # forearm is 48 x 46 mm
HEAD_R, HEAD_HALF = 30.0, 26.0
SLOT_Y = 13.5                 # wrist link fits between these tines
RIB = (5.0, 6.5)
Y_S1 = 7.5                    # stage 1 belt plane
Y_S2 = 14.0                   # stage 2 belt plane
BELT_H = 6.0

# Bearings: 2 x 6802 (15 x 24 x 5) in the tines. Compound pulley: 2 x 625 (5 x 16 x 5).
B_ID, B_OD, B_W = 15.0, 24.0, 5.0
FIT = 0.15

# Stage 1: 20T on the motor to 60T, 160 mm belt. Stage 2: 16T to 80T, 300 mm belt.
PITCH = 2.0
pd = lambda t: t * PITCH / math.pi


def centre_distance(t1, t2, length):
    d, D = pd(t1), pd(t2)
    lo, hi = 10.0, 300.0
    for _ in range(60):
        c = (lo + hi) / 2
        l = 2 * c + math.pi * (D + d) / 2 + (D - d) ** 2 / (4 * c)
        lo, hi = (c, hi) if l < length else (lo, c)
    return c


C1 = centre_distance(20, 60, 160.0)
C2 = centre_distance(16, 80, 300.0)
X_C = X_W - C2                # compound pulley shaft
Z_C = Z_E
MOTOR_W, MOTOR_L = 42.3, 20.0 # 17HS08-1004S, CHECK
HUMP_Z = 27.0
Z_MOT = Z_E + HUMP_Z
X_MOT = X_C - math.sqrt(C1 ** 2 - HUMP_Z ** 2)
TENSION = 2.5


def sec(x, hy, hz, yc=0.0, r=10.0):
    pts = [(yc + sy * (hy - r), sz * (hz - r)) for sy in (-1, 1) for sz in (-1, 1)]
    return Manifold.batch_hull([Manifold.cylinder(0.01, r, r, 64).rotate((0, 90, 0)).translate((x, y, Z_E + z)) for y, z in pts])


def skin(off):
    r = 10.0 - off * 0.8
    hy, hz = HALF_Y - off, HALF_Z - off
    stem_hy = (STEM_Y[1] - STEM_Y[0]) / 2 - off
    root = Manifold.batch_hull([sec(X_ROOT, stem_hy, hz, STEM_C, r), sec(X_ROOT + 42, hy, hz, 0, r)])
    tube = Manifold.batch_hull([sec(X_ROOT + 42, hy, hz, 0, r), sec(X_W - 34, hy, hz, 0, r)])
    head = Manifold.batch_hull([sec(X_W - 34, hy, hz, 0, r), ycyl(-HEAD_HALF + off, HEAD_HALF - off, HEAD_R - off, X_W, Z_E)])
    hump = Manifold.batch_hull([box(X_MOT - 25 + off, X_MOT + 25 - off, -18 + off, 17 - off, Z_E + 12, Z_E + 16),
                                ycyl(-18 + off, 17 - off, 14 - off, X_MOT - 12.5, Z_MOT + 15),
                                ycyl(-18 + off, 17 - off, 14 - off, X_MOT + 12.5, Z_MOT + 15)])
    return root + tube + head + hump


LID_X = (X_ROOT + 46, X_W - 42)
SPIGOT_X = (X_ROOT - 16, X_ROOT - 6)
LID_SCREW_Y = (-18.0, 3.0)    # the belt runs on the +Y side, so that side screws to the rib


def forearm():
    body = skin(0) - skin(WALL)

    # Rib between wires and belts.
    rib = box(X_ROOT + 10, X_W - 34, RIB[0], RIB[1], Z_E - HALF_Z, Z_MOT + 30) ^ skin(1)
    body += rib

    # Spigot that slides into the elbow stem.
    hy0, hy1 = STEM_Y[0] + 3.2, STEM_Y[1] - 3.2
    spigot = box(X_ROOT - 22, X_ROOT + 2, hy0, hy1, Z_E - 18.8, Z_E + 18.8) - box(X_ROOT - 23, X_ROOT + 3, hy0 + 2.5, hy1 - 2.5, Z_E - 16.3, Z_E + 16.3)
    body += spigot

    cuts = []
    for x in SPIGOT_X:                                       # M3 bolts through the stem and spigot
        cuts.append(Manifold.cylinder(60, 1.5, 1.5, 32).translate((x, STEM_C, Z_E - 30)))
    # Wrist fork: the link swings between the tines, with room behind the axis for J4 travel.
    cuts.append(box(X_W - 58, X_W + 40, -SLOT_Y, SLOT_Y, Z_E - 40, Z_E + 40))
    # Belt bay in the +Y tine, and the 80T pulley.
    cuts.append(ycyl(SLOT_Y - 1, HEAD_HALF - B_W, HEAD_R - 2.5, X_W, Z_E))
    # Bearing seats from the outside.
    for sy in (-1, 1):
        y0, y1 = sorted((sy * (HEAD_HALF - B_W), sy * (HEAD_HALF + 1)))
        cuts.append(ycyl(y0, y1, (B_OD + 2 * FIT) / 2, X_W, Z_E))
    # Lid opening on the underside.
    cuts.append(box(LID_X[0], LID_X[1], -HALF_Y + WALL - 0.2, HALF_Y - WALL + 0.2, Z_E - HALF_Z - 1, Z_E - 8))
    # Motor mount: slots along the belt.
    ux, uz = (X_C - X_MOT) / C1, -HUMP_Z / C1
    ends = (-TENSION, TENSION)
    cuts.append(Manifold.batch_hull([ycyl(RIB[0] - 1, RIB[1] + 1, 12, X_MOT + e * ux, Z_MOT + e * uz) for e in ends]))
    for sx in (-1, 1):
        for sz in (-1, 1):
            cuts.append(Manifold.batch_hull([ycyl(RIB[0] - 1, RIB[1] + 1, 1.8, X_MOT + sx * 15.5 + e * ux, Z_MOT + sz * 15.5 + e * uz) for e in ends]))
    # Compound pulley bolt, slotted along stage 2 for tension.
    cuts.append(Manifold.batch_hull([ycyl(RIB[0] - 1, RIB[1] + 1, 2.7, X_C + e, Z_C) for e in ends]))
    cuts.append(Manifold.batch_hull([ycyl(HALF_Y - WALL - 1, HALF_Y + 1, 2.7, X_C + e, Z_C) for e in ends]))
    for c in cuts:
        body -= c

    for x in lid_screw_x():
        for y in LID_SCREW_Y:
            y0, y1 = (-HALF_Y + 1, -13) if y < 0 else (0.0, RIB[1])
            post = box(x - 4.5, x + 4.5, y0, y1, Z_E - 13, Z_E - 6) ^ skin(1)
            body = body + post - Manifold.cylinder(10, 1.5, 1.5, 32).translate((x, y, Z_E - 15))
    return body


def lid_screw_x():
    return (138.0, 151.0)     # clear of the compound pulley and the wrist slot


def forearm_lid():
    plate = (skin(0) - skin(WALL)) ^ box(LID_X[0] + 0.2, LID_X[1] - 0.2, -HALF_Y + WALL, HALF_Y - WALL, Z_E - HALF_Z - 1, Z_E - 8.2)
    for x in lid_screw_x():
        for y in LID_SCREW_Y:
            plate -= Manifold.cylinder(30, 1.7, 1.7, 32).translate((x, y, Z_E - 30))
    # Clips: rotate the arm clip so its prongs stand up from the lid and its bundle runs along X.
    for x in (LID_X[0] + 10, LID_X[1] - 8):
        c = clip_profile(0, 1, 0, -4)
        c = c.rotate((0, -90, 0)).translate((x, -8.0, Z_E - HALF_Z + WALL - 0.6))
        plate += c
    return plate


def compound_pulley():
    """60T and 16T on one printed part, running on 2 x 625 bearings on an M5 bolt."""
    teeth = lambda t, y0, h: _toothed(t, y0, h)
    body = teeth(60, Y_S1, BELT_H + 0.5) + teeth(16, Y_S2, BELT_H + 0.8)
    body += ycyl(Y_S1 - 0.8, Y_S1, pd(60) / 2 + 0.6, X_C, Z_C)
    body += ycyl(Y_S1 + BELT_H + 0.5, Y_S1 + BELT_H + 1.1, pd(60) / 2 + 0.6, X_C, Z_C)
    body -= ycyl(Y_S1 - 2, Y_S2 + BELT_H + 2, 2.7 + 1.6, X_C, Z_C)
    body -= ycyl(Y_S1 - 2, Y_S1 + 5, 8.1, X_C, Z_C)
    return body


def _toothed(t, y0, h, x=None, z=None, trim=0.25):
    x = X_C if x is None else x
    z = Z_C if z is None else z
    r = pd(t) / 2 - trim
    wheel = ycyl(y0, y0 + h, r, x, z)
    g = [ycyl(y0 - 0.1, y0 + h + 0.1, 0.55, x + r * math.cos(2 * math.pi * i / t), z + r * math.sin(2 * math.pi * i / t)) for i in range(t)]
    return wheel - Manifold.compose(g)


def wrist_pulley():
    body = _toothed(80, Y_S2, BELT_H + 0.8, X_W, Z_E)
    body += ycyl(Y_S2 - 0.5, Y_S2, pd(80) / 2 + 1.2, X_W, Z_E)
    body += ycyl(Y_S2 + BELT_H + 0.8, Y_S2 + BELT_H + 1.3, pd(80) / 2 + 1.2, X_W, Z_E)
    body += ycyl(SLOT_Y - 0.3, Y_S2, 19, X_W, Z_E)
    body += ycyl(Y_S2 + BELT_H, HEAD_HALF - 0.2, (B_ID - FIT) / 2, X_W, Z_E)
    for i in range(3):
        t = math.radians(30 + 120 * i)
        body -= ycyl(SLOT_Y - 1, Y_S2 + 10, 1.7, X_W + 14 * math.cos(t), Z_E + 14 * math.sin(t))
    return body


def wrist_link():
    """Turns between the tines. The J5 housing bolts to its front face."""
    hub = ycyl(-SLOT_Y + 0.4, SLOT_Y - 0.4, 21, X_W, Z_E)
    neck = Manifold.batch_hull([ycyl(-SLOT_Y + 0.4, SLOT_Y - 0.4, 21, X_W, Z_E), box(X_W + 36, X_W + 38, -SLOT_Y + 0.4, SLOT_Y - 0.4, Z_E - 18, Z_E + 18)])
    axle = ycyl(-HEAD_HALF + 0.2, -SLOT_Y + 0.5, (B_ID - FIT) / 2, X_W, Z_E)
    body = hub + neck + axle
    body -= box(X_W + 6, X_W + 39, -9.5, 9.5, Z_E - 13, Z_E + 13)                # wires pass through
    body -= box(X_W - 22, X_W + 8, -9.5, 9.5, Z_E - 8, Z_E + 8)
    body -= ycyl(-HEAD_HALF - 1, -HEAD_HALF + 2.7, 3.1, X_W, Z_E)                # magnet
    for i in range(3):
        t = math.radians(30 + 120 * i)
        body -= ycyl(SLOT_Y - 8, SLOT_Y + 1, 1.5, X_W + 14 * math.cos(t), Z_E + 14 * math.sin(t))
    return body


def dummy_motor():
    can = box(X_MOT - MOTOR_W / 2, X_MOT + MOTOR_W / 2, RIB[0] - MOTOR_L, RIB[0], Z_MOT - MOTOR_W / 2, Z_MOT + MOTOR_W / 2)
    shaft = ycyl(RIB[1] + 0.1, Y_S1 + BELT_H, 2.5, X_MOT, Z_MOT)
    pulley = ycyl(Y_S1, Y_S1 + BELT_H, pd(20) / 2, X_MOT, Z_MOT)
    return can + shaft + pulley


J3_MAX = 50                   # the forearm reaches the upper arm past this


def hinge(m, deg):
    return m.translate((-X_W, 0, -Z_E)).rotate((0, deg, 0)).translate((X_W, 0, Z_E))


def main():
    parts = {'j4_forearm': forearm(), 'j4_forearm_lid': forearm_lid(), 'j4_compound_pulley': compound_pulley(),
             'j4_wrist_pulley': wrist_pulley(), 'j4_wrist_link': wrist_link()}
    print('Parts:')
    for name, m in parts.items():
        lo, hi = m.bounding_box()[:3], m.bounding_box()[3:]
        tm = to_trimesh(m)
        assert tm.is_watertight, name
        n = len(m.decompose())
        print(f'  {name:18} {[round(b - a, 1) for a, b in zip(lo, hi)]} mm, about {m.volume() / 1000 * 1.27 * 0.6:.0f} g, {n} piece(s)')
        if n > 1:
            print('   pieces:', [[round(v) for v in q.bounding_box()] for q in m.decompose()])
        tm.export(OUT / f'{name}.stl')
        bad_piece = n != 1
        assert not bad_piece, f'{name} is not one piece'
    f, l, cp, wp, wl = (parts[k] for k in ('j4_forearm', 'j4_forearm_lid', 'j4_compound_pulley', 'j4_wrist_pulley', 'j4_wrist_link'))
    mot = dummy_motor()
    bad = 0

    def check(na, a, nb, b):
        nonlocal bad
        v = (a ^ b).volume()
        print(f'  {na:14} vs {nb:14}: {v:8.2f} mm3 {"OK" if v < 1 else "COLLISION"}')
        bad += v >= 1

    print('Static:')
    stem = elbow_stem()
    check('forearm', f, 'lid', l)
    check('forearm', f, 'stem', stem)
    check('forearm', f, 'compound', cp)
    check('forearm', f, 'wrist pulley', wp)
    check('forearm', f, 'motor', mot - ycyl(RIB[0] - 1, RIB[1] + 1, 11, X_MOT, Z_MOT))
    check('compound', cp, 'motor', mot)
    check('compound', cp, 'wrist pulley', wp)
    check('wrist link', wl, 'wrist pulley', wp)
    print('J4 travel, -110 to +110 deg:')
    w = {}
    for d in range(-110, 111, 10):
        moved = hinge(wl + wp, d)
        for n, m in (('forearm', f), ('lid', l), ('compound', cp)):
            w[n] = max(w.get(n, 0), (moved ^ m).volume())
    for n, v in w.items():
        print(f'  wrist vs {n:9}: {v:8.2f} mm3 {"OK" if v < 1 else "COLLISION"}')
        bad += v >= 1
    print('J3 travel of the forearm:')
    arm, alid, jm = upper_arm(), arm_lid(), dummy_j3_motor()
    fore = f + l + mot + hinge(wl, 0)
    worst_ok = None
    for d in range(-80, 81, 5):
        moved = bend(fore, d)
        v = max((moved ^ m).volume() for m in (arm, alid, jm))
        print(f'  J3 {d:+4d}: {v:9.1f} mm3 {"OK" if v < 1 else "COLLISION"}')
        if -80 <= d <= J3_MAX:
            bad += v >= 1
    print(f'  stage 1 centre {C1:.1f}, stage 2 centre {C2:.1f}, shaft x {X_C:.1f}, motor x {X_MOT:.1f}, z {Z_MOT:.1f}')
    print('ALL CHECKS PASSED' if not bad else f'{bad} PROBLEMS')


if __name__ == '__main__':
    main()
