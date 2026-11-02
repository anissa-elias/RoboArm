"""J3 elbow and slim upper arm for RoboArm. All dimensions in mm, same frame as base_j1.py.

    pip install manifold3d trimesh numpy
    python j3_elbow.py

The upper arm is a hollow tunnel with a screw-on lid. A rib splits it into a wire tunnel (-Y)
and a belt bay (+Y). Clips on the lid hold the wires. +X is the front of the arm at J2 = 0.
Writes STL files to ../stl/ and checks fit through the J2 and J3 travel.
Measure before printing: anything marked CHECK came from a generic drawing.
"""
import math

from manifold3d import Manifold

from base_j1 import OUT, box, cyl, to_trimesh, rotor, base_shell, deck, belt_cover
from j2_shoulder import (Z_J2, Z_ROOT_TOP, ROOT_BOLT_X, ROOT_BOLT_Y, arm_root, big_pulley, dummy_motor as j2_motor,
                         housing, swing, ycyl)

Z_E = Z_J2 + 221.0            # elbow axis
WALL = 3.0
HALF_Y = 30.0                 # arm is 60 mm wide
RIB_Y = (2.0, 5.0)            # wall between the wires and the belt
HEAD_Y = 37.0                 # elbow head half width
Z_LID_TOP = Z_E - 92.0        # lid stops where the forearm folds in
Z_LID_LOW = Z_ROOT_TOP + 10.0

# Elbow bearings: 2 x 6804 (20 x 32 x 7), one in each cheek.
B_ID, B_OD, B_W = 20.0, 32.0, 7.0
FIT = 0.15

# J3 belt: 16T on the gearbox shaft, 80T on the elbow, 380 mm 15 mm GT2 loop.
TEETH_S, TEETH_B, PITCH, BELT_LEN = 16, 80, 2.0, 380.0
PD_S, PD_B = TEETH_S * PITCH / math.pi, TEETH_B * PITCH / math.pi
Y_BELT = 8.0
PULLEY_H = 17.0
FLANGE_R = PD_B / 2 + 1.5


def centre_distance():
    lo, hi = 100.0, 220.0
    for _ in range(60):
        c = (lo + hi) / 2
        length = 2 * c + math.pi * (PD_B + PD_S) / 2 + (PD_B - PD_S) ** 2 / (4 * c)
        lo, hi = (c, hi) if length < BELT_LEN else (lo, c)
    return c


# Motor sits in a slim hump at the back, so the wires pass in front of the gearbox.
# CHECK against the 17HS19-1684S-PG5 datasheet when it arrives.
MOTOR_W, MOTOR_L, GBOX_D, GBOX_L = 42.3, 48.0, 36.0, 33.0
GBOX_BOSS_D, GBOX_PCD, GBOX_BOLT = 22.0, 28.0, 4.5
CENTRE = centre_distance()
X_M = -27.0
Z_M = Z_E - math.sqrt(CENTRE ** 2 - X_M ** 2)
Y_FACE = RIB_Y[0]             # gearbox bolts to the rib
TENSION = 3.0


def slab(z, x0, x1, half_y, r=12.0):
    pts = [(x0 + r, -half_y + r), (x0 + r, half_y - r), (x1 - r, -half_y + r), (x1 - r, half_y - r)]
    return Manifold.batch_hull([cyl(0.01, r, z, x, y) for x, y in pts])


def shell(off):
    """Outer skin of the arm, offset inwards by off."""
    r = 12.0 - off
    hy = HALF_Y - off
    return Manifold.batch_hull([slab(Z_ROOT_TOP, -20 + off, 20 - off, 26 - off, r), slab(Z_M + 22, -26 + off, 25 - off, hy, r)]) + \
        Manifold.batch_hull([slab(Z_M + 22, -26 + off, 25 - off, hy, r), slab(Z_E - 40, -24 + off, 24 - off, hy, r)]) + \
        Manifold.batch_hull([ycyl(-hy, hy, 23 - off, X_M, Z_M), slab(Z_M + 30, -24 + off, 20 - off, hy, r), slab(Z_M - 26, -19 + off, 10, hy - 3, r)])


def head(off=0.0):
    return Manifold.batch_hull([ycyl(-HEAD_Y + off, HEAD_Y - off, 34 - off, 0, Z_E), slab(Z_E - 48, -24 + off, 24 - off, HALF_Y - off, 12 - off)])


def upper_arm():
    body = shell(0) + head()
    body -= shell(WALL)
    # Solid floor with bolts down into the arm root, and a wire opening.
    body += box(-20, 20, -26, 26, Z_ROOT_TOP, Z_ROOT_TOP + 5) ^ shell(0)
    # Rib between wires and belt, with the gearbox bolted to it.
    body += box(-40, 30, RIB_Y[0], RIB_Y[1], Z_ROOT_TOP + 5, Z_E - 44) ^ shell(1)

    # Hollow out the head: belt bay and the slot the forearm swings in.
    bay = ycyl(RIB_Y[1], HEAD_Y - 9, 31, 0, Z_E)
    body -= bay
    body -= Manifold.batch_hull([box(-21, 21, RIB_Y[1], HALF_Y - WALL, Z_E - 48, Z_E - 44), ycyl(RIB_Y[1], HALF_Y - WALL, 29, 0, Z_E)])
    slot_y = (-HEAD_Y + 9, RIB_Y[1])
    body -= box(-24, 80, slot_y[0], slot_y[1], Z_LID_TOP, Z_E + 80)         # forearm folds down the front
    body -= box(-80, 80, slot_y[0], slot_y[1], Z_E - 8, Z_E + 80)           # and swings up over the top

    cuts = [box(1, 60, -HALF_Y + WALL - 0.2, HALF_Y - WALL + 0.2, Z_LID_LOW, Z_LID_TOP)]   # lid opening
    cuts.append(box(-16, 16, -25, -4, Z_ROOT_TOP - 1, Z_ROOT_TOP + 7))                                  # wires from the arm root
    for sx in (-1, 1):
        for sy in (-1, 1):
            cuts.append(cyl(8, 2.3, Z_ROOT_TOP - 1, sx * ROOT_BOLT_X, sy * ROOT_BOLT_Y))
    for sy in (-1, 1):
        y0, y1 = sorted((sy * (HEAD_Y - 9), sy * (HEAD_Y - 9 + B_W + 0.5)))
        cuts.append(ycyl(y0, y1, (B_OD + 2 * FIT) / 2, 0, Z_E))
        y0, y1 = sorted((sy * (HEAD_Y - 2), sy * (HEAD_Y + 1)))
        cuts.append(ycyl(y0, y1, 13, 0, Z_E))
    # Motor mount in the rib; slots run along the belt for tension.
    ux, uz = -X_M / CENTRE, (Z_E - Z_M) / CENTRE
    ends = (-TENSION, TENSION)
    cuts.append(Manifold.batch_hull([ycyl(Y_FACE - 1, RIB_Y[1] + 1, GBOX_BOSS_D / 2 + 1, X_M + e * ux, Z_M + e * uz) for e in ends]))
    for i in range(4):
        t = math.radians(45 + 90 * i)
        ox, oz = GBOX_PCD / 2 * math.cos(t), GBOX_PCD / 2 * math.sin(t)
        cuts.append(Manifold.batch_hull([ycyl(Y_FACE - 1, RIB_Y[1] + 1, GBOX_BOLT / 2, X_M + ox + e * ux, Z_M + oz + e * uz) for e in ends]))
    # The gearbox and motor pass out through the -Y wall.
    cuts.append(ycyl(-HALF_Y - 1, Y_FACE, GBOX_D / 2 + 0.5, X_M, Z_M))
    for c in cuts:
        body -= c

    for z in lid_screw_z():
        for y in (-22.0, 22.0):
            y0, y1 = sorted((math.copysign(17.5, y), math.copysign(HALF_Y - 1, y)))
            post = box(-6, 0.8, y0, y1, z - 4.5, z + 4.5) ^ shell(1)
            hole = Manifold.cylinder(14, 1.5, 1.5, 32).rotate((0, 90, 0)).translate((-7, y, z))
            body = body + post - hole

    # Two rear wire clips above the motor.
    for z in (Z_M + 36, Z_LID_TOP - 16):
        body += rear_clip(z)
    return body


def lid_screw_z():
    return (Z_LID_LOW + 12, (Z_LID_LOW + Z_LID_TOP) / 2, Z_LID_TOP - 12)


def clip_profile(x_base, direction, y, z, gap=9.0, inner=15.0, length=16.0, depth=8.0):
    """U clip with barbs. Open end faces the tunnel. Snap a wire bundle up to 15 mm in."""
    legs = []
    for sy in (-1, 1):
        y0 = y + sy * inner / 2
        y1 = y0 + sy * 2.5
        a, b = sorted((y0, y1))
        x0, x1 = sorted((x_base, x_base + direction * length))
        legs.append(box(x0, x1, a, b, z, z + depth))
        c, d = sorted((y + sy * gap / 2, y0 + sy * 0.1))
        bx0, bx1 = sorted((x_base + direction * (length - 3), x_base + direction * length))
        legs.append(box(bx0, bx1, c, d, z, z + depth))
    return legs[0] + legs[1] + legs[2] + legs[3]


def rear_clip(z):
    x_wall = -24.0
    return clip_profile(x_wall, 1, -14.0, z)


def lid():
    outer = shell(0)
    plate = outer ^ box(1, 60, -HALF_Y + WALL, HALF_Y - WALL, Z_LID_LOW + 0.2, Z_LID_TOP - 0.2)
    plate -= shell(WALL) ^ box(-60, 60, -60, 60, Z_LID_LOW - 1, Z_LID_TOP + 1)
    for z in lid_screw_z():
        for y in (-22.0, 22.0):
            plate -= Manifold.cylinder(70, 1.7, 1.7, 32).rotate((0, 90, 0)).translate((-5, y, z))
    x_in = 23.5
    mid = plate
    for z in (Z_LID_LOW + 26, (Z_LID_LOW + Z_LID_TOP) / 2 + 8, Z_LID_TOP - 30):
        mid += clip_profile(x_in, -1, -14.0, z)
    return mid


def elbow_stem():
    """Forearm root. Turns in the head; the forearm bolts to its front. Wires enter at the back."""
    hy0, hy1 = -HEAD_Y + 9.6, RIB_Y[1] - 0.4
    hub = ycyl(hy0, hy1, 25, 0, Z_E)
    arm = Manifold.batch_hull([ycyl(hy0, hy1, 25, 0, Z_E), box(58, 60, hy0, hy1, Z_E - 22, Z_E + 22)])
    axle = ycyl(-HEAD_Y + 2, hy0 + 0.1, (B_ID - FIT) / 2, 0, Z_E) + ycyl(-HEAD_Y + 8.5, hy0 + 0.1, 13, 0, Z_E)
    body = hub + arm + axle
    tunnel = box(10, 61, hy0 + 3, hy1 - 3, Z_E - 19, Z_E + 19)
    window = Manifold.batch_hull([box(10, 12, hy0 + 3, hy1 - 3, Z_E - 19, Z_E + 19), box(-12, -10, hy0 + 3, hy1 - 3, Z_E - 12, Z_E + 12)])
    body -= tunnel
    body -= window
    body -= box(-30, 8, hy0 - 1, hy1 + 1, Z_E - 40, Z_E - 15) ^ ycyl(hy0 - 1, hy1 + 1, 40, 0, Z_E)  # bundle enters from below
    body -= ycyl(-HEAD_Y + 1, -HEAD_Y + 2 + 2.5, 3.1, 0, Z_E)                    # magnet
    for x in (44.0, 54.0):                                                       # M3 bolts into the forearm spigot
        body -= Manifold.cylinder(60, 1.7, 1.7, 32).translate((x, (hy0 + hy1) / 2, Z_E - 30))
    for i in range(3):
        t = math.radians(30 + 120 * i)
        body -= ycyl(hy1 - 10, hy1 + 1, 1.5, 19 * math.cos(t), Z_E + 19 * math.sin(t))
    return body


def elbow_pulley():
    y0 = Y_BELT
    wheel = ycyl(y0, y0 + PULLEY_H, PD_B / 2 - 0.25, 0, Z_E)
    grooves = []
    for i in range(TEETH_B):
        t = 2 * math.pi * i / TEETH_B
        r = PD_B / 2 - 0.25
        grooves.append(ycyl(y0 - 0.1, y0 + PULLEY_H + 0.1, 0.6, r * math.cos(t), Z_E + r * math.sin(t)))
    wheel -= Manifold.compose(grooves)
    body = wheel + ycyl(y0 - 1.4, y0, FLANGE_R, 0, Z_E) + ycyl(y0 + PULLEY_H, y0 + PULLEY_H + 1.4, FLANGE_R, 0, Z_E)
    body += ycyl(RIB_Y[1], y0, 25, 0, Z_E)                                       # spacer to the stem
    body += ycyl(y0 + PULLEY_H, HEAD_Y - 2, (B_ID - FIT) / 2, 0, Z_E)            # axle into the +Y bearing
    for i in range(3):
        t = math.radians(30 + 120 * i)
        body -= ycyl(RIB_Y[1] - 1, y0 + PULLEY_H + 3, 1.7, 19 * math.cos(t), Z_E + 19 * math.sin(t))
        body -= ycyl(y0 + 5, y0 + PULLEY_H + 3, 3.2, 19 * math.cos(t), Z_E + 19 * math.sin(t))
    return body


def dummy_j3_motor():
    gbox = ycyl(Y_FACE - GBOX_L, Y_FACE, GBOX_D / 2, X_M, Z_M)
    y0 = Y_FACE - GBOX_L - MOTOR_L
    can = box(X_M - MOTOR_W / 2, X_M + MOTOR_W / 2, y0, Y_FACE - GBOX_L, Z_M - MOTOR_W / 2, Z_M + MOTOR_W / 2)
    shaft = ycyl(RIB_Y[1] + 0.1, Y_BELT + 12, 4, X_M, Z_M)
    pulley = ycyl(Y_BELT, Y_BELT + PULLEY_H, PD_S / 2 + 0.6, X_M, Z_M)
    return gbox + can + shaft + pulley


def bend(m, deg):
    """J3: positive folds the forearm down the front of the arm."""
    return m.translate((0, 0, -Z_E)).rotate((0, deg, 0)).translate((0, 0, Z_E))


def main():
    parts = {'j3_upper_arm': upper_arm(), 'j3_arm_lid': lid(), 'j3_elbow_stem': elbow_stem(), 'j3_elbow_pulley': elbow_pulley()}
    print('Parts:')
    for name, m in parts.items():
        lo, hi = m.bounding_box()[:3], m.bounding_box()[3:]
        tm = to_trimesh(m)
        tm.merge_vertices()
        assert tm.is_watertight, name
        n = len(m.decompose())
        if n > 1:
            print('   pieces:', [[round(v) for v in q.bounding_box()] for q in m.decompose()])
        print(f'  {name:16} {[round(b - a, 1) for a, b in zip(lo, hi)]} mm, about {m.volume() / 1000 * 1.27 * 0.6:.0f} g, {n} piece(s)')
        assert n == 1, f'{name} is not one piece'
        tm.export(OUT / f'{name}.stl')

    bad = 0

    def check(na, a, nb, b, limit=1.0):
        nonlocal bad
        v = (a ^ b).volume()
        print(f'  {na:14} vs {nb:14}: {v:8.2f} mm3 {"OK" if v < limit else "COLLISION"}')
        bad += v >= limit

    arm, l, s, p = parts['j3_upper_arm'], parts['j3_arm_lid'], parts['j3_elbow_stem'], parts['j3_elbow_pulley']
    motor = dummy_j3_motor()
    print('Static:')
    check('upper arm', arm, 'lid', l)
    check('upper arm', arm, 'arm root', arm_root())
    check('upper arm', arm, 'motor', motor - ycyl(RIB_Y[0] - 1, RIB_Y[1] + 1, 13, X_M, Z_M))
    check('upper arm', arm, 'pulley', p)
    check('lid', l, 'motor', motor)
    check('stem', s, 'pulley', p)
    print('J3 travel, -80 to +50 deg:')
    worst = {}
    for d in range(-80, 51, 10):
        moved = bend(s + p, d)
        for n, m in (('upper arm', arm), ('lid', l), ('motor', motor)):
            worst[n] = max(worst.get(n, 0), (moved ^ m).volume())
    for n, v in worst.items():
        print(f'  elbow vs {n:10}: {v:8.2f} mm3 {"OK" if v < 1 else "COLLISION"}')
        bad += v >= 1
    print('J2 travel, -35 to +90 deg:')
    fixed = {'housing': housing(), 'J2 motor': j2_motor(), 'turntable': rotor(), 'belt cover': belt_cover(), 'deck': deck()}
    moving = arm + l + motor
    worst = {}
    for d in range(-35, 91, 5):
        moved = swing(moving, d)
        for n, m in fixed.items():
            worst[n] = max(worst.get(n, 0), (moved ^ m).volume())
    for n, v in worst.items():
        print(f'  upper arm vs {n:10}: {v:8.2f} mm3 {"OK" if v < 1 else "COLLISION"}')
        bad += v >= 1
    print(f'  belt centre distance {CENTRE:.2f} mm, motor at x {X_M:.1f}, z {Z_M:.1f}')
    print('ALL CHECKS PASSED' if not bad else f'{bad} PROBLEMS')


if __name__ == '__main__':
    main()
