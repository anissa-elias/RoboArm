"""J2 shoulder for RoboArm. All dimensions in mm, same frame as base_j1.py.

    pip install manifold3d trimesh numpy
    python j2_shoulder.py

The J2 axis runs along Y at x = 0, z = 166. The arm points up at J2 = 0 and tips towards +X.
Writes STL files to ../stl/ and checks fit through the full J2 travel.
Measure before printing: anything marked CHECK came from a generic drawing.
"""
import math

from manifold3d import Manifold

from base_j1 import OUT, PD_MOTOR, Z_ROTOR_TOP, J2_BOLT_SQ, box, cyl, rotor, to_trimesh

Z_J2 = 166.0
PLATE_T = 6.0
Z_PLATE_TOP = Z_ROTOR_TOP + PLATE_T

# Bearings: 2 x 6806 (30 x 42 x 7), one in each tower.
B_ID, B_OD, B_W = 30.0, 42.0, 7.0
FIT = 0.15
TOWER_IN, TOWER_OUT = 30.0, 43.0
BORE_CLEAR = 34.0

# J2 belt: 20T on the gearbox shaft, 100T on the arm, 280 mm 15 mm GT2 loop.
TEETH_BIG, BELT_PITCH, BELT_LEN = 100, 2.0, 280.0
PD_BIG = TEETH_BIG * BELT_PITCH / math.pi
BELT_W = 15.0
Y_PULLEY = 45.0
PULLEY_H = BELT_W + 2.0
FLANGE_R = PD_BIG / 2 + 1.5


def centre_distance():
    d, D = PD_MOTOR, PD_BIG
    lo, hi = 40.0, 140.0
    for _ in range(60):
        c = (lo + hi) / 2
        length = 2 * c + math.pi * (D + d) / 2 + (D - d) ** 2 / (4 * c)
        lo, hi = (c, hi) if length < BELT_LEN else (lo, c)
    return c


CENTRE = centre_distance()

# Motor, CHECK against the 17HS19-1684S-PG14 datasheet when it arrives.
MOTOR_W, MOTOR_L, GBOX_D, GBOX_L, SHAFT_L = 42.3, 48.0, 36.0, 46.0, 24.0
GBOX_BOSS_D, GBOX_PCD, GBOX_BOLT = 22.0, 28.0, 4.5
Y_FACE = 33.0                     # gearbox face against the motor wall
WALL_T = 6.0
Z_MOTOR = Z_PLATE_TOP + MOTOR_W / 2 + 0.5
X_MOTOR = -math.sqrt(CENTRE ** 2 - (Z_J2 - Z_MOTOR) ** 2)
TENSION = 3.0

# Arm root
ROOT_R, ROOT_HALF = 28.0, 28.5
SOCKET, SOCKET_Y, SOCKET_DEPTH = 20.3, 14.0, 35.0
Z_ROOT_TOP = Z_J2 + 50.0
HUB_D = B_ID - FIT
Y_HUB_MAG, Y_HUB_PULLEY = -42.0, TOWER_OUT
MAG_D, MAG_H = 6.2, 2.5
PULLEY_BOLT_PCD = 22.0


def ycyl(y0, y1, r, x=0.0, z=Z_J2):
    """Cylinder along Y from y0 to y1."""
    return Manifold.cylinder(y1 - y0, r, r, 128).rotate((-90, 0, 0)).translate((x, y0, z))


def housing():
    q = J2_BOLT_SQ / 2
    plate = box(-108, 50, -46, 43, Z_ROTOR_TOP, Z_PLATE_TOP)
    body = plate
    for sy in (-1, 1):
        y0, y1 = sorted((sy * TOWER_IN, sy * TOWER_OUT))
        tower = Manifold.batch_hull([box(-34, 34, y0, y1, Z_ROTOR_TOP, Z_PLATE_TOP + 1), ycyl(y0, y1, 30)])
        body += tower
    wall = box(X_MOTOR - 32, -28, Y_FACE, Y_FACE + WALL_T, Z_ROTOR_TOP, Z_MOTOR + 26)
    body += wall
    for sx in (-14, 14):                                     # encoder bracket posts
        body += box(sx - 3, sx + 3, -50, -TOWER_OUT + 0.1, Z_J2 - 16, Z_J2 + 16)
    body += box(-17, 17, -50, -47, Z_J2 - 16, Z_J2 + 16)     # AS5600 pad

    cuts = [box(-38, 38, -29.5, 29.5, Z_ROTOR_TOP - 1, Z_PLATE_TOP + 1)]  # cables, and clearance for the arm barrel
    cuts += [cyl(PLATE_T + 2, 2.3, Z_ROTOR_TOP - 1, sx * q, sy * q) for sx in (-1, 1) for sy in (-1, 1)]
    for sy in (-1, 1):
        y0, y1 = sorted((sy * TOWER_IN, sy * (TOWER_IN + B_W + 1)))
        cuts.append(ycyl(y0, y1, (B_OD + 2 * FIT) / 2))      # bearing seat, from the inside
        y0, y1 = sorted((sy * (TOWER_IN - 1), sy * (TOWER_OUT + 1)))
        cuts.append(ycyl(y0, y1, BORE_CLEAR / 2))
    # Motor wall: slots run along the belt so the motor slides to set tension.
    a = math.atan2(Z_MOTOR - Z_J2, X_MOTOR)
    ux, uz = math.cos(a), math.sin(a)
    ends = (-TENSION, TENSION)
    cuts.append(Manifold.batch_hull([ycyl(Y_FACE - 1, Y_FACE + WALL_T + 1, GBOX_BOSS_D / 2 + 1, X_MOTOR + e * ux, Z_MOTOR + e * uz) for e in ends]))
    for i in range(4):
        t = math.radians(45 + 90 * i)
        ox, oz = GBOX_PCD / 2 * math.cos(t), GBOX_PCD / 2 * math.sin(t)
        cuts.append(Manifold.batch_hull([ycyl(Y_FACE - 1, Y_FACE + WALL_T + 1, GBOX_BOLT / 2, X_MOTOR + ox + e * ux, Z_MOTOR + oz + e * uz) for e in ends]))
    for sx in (-8.5, 8.5):                                   # AS5600 module screws, CHECK
        for sz in (-8.5, 8.5):
            cuts.append(ycyl(-52, -45, 1.2, sx, Z_J2 + sz))
    for c in cuts:
        body -= c
    return body


def arm_root():
    barrel = ycyl(-ROOT_HALF, ROOT_HALF, ROOT_R)
    neck = box(-17, 17, -ROOT_HALF, ROOT_HALF, Z_J2, Z_ROOT_TOP)
    collar = ycyl(-TOWER_IN, -ROOT_HALF + 0.1, 18) + ycyl(ROOT_HALF - 0.1, TOWER_IN, 18)
    hub = ycyl(Y_HUB_MAG, -TOWER_IN + 0.1, HUB_D / 2) + ycyl(TOWER_IN - 0.1, Y_HUB_PULLEY, HUB_D / 2)
    tab = box(-27, -16, -6, 6, Z_J2 + 30, Z_J2 + 44)          # spring anchor
    body = barrel + neck + collar + hub + tab

    cuts = []
    for sy in (-1, 1):
        y = sy * SOCKET_Y
        cuts.append(box(-SOCKET / 2, SOCKET / 2, y - SOCKET / 2, y + SOCKET / 2, Z_ROOT_TOP - SOCKET_DEPTH, Z_ROOT_TOP + 1))
        for z in (Z_ROOT_TOP - 10, Z_ROOT_TOP - 25):          # M4 through bolts into the extrusion
            cuts.append(Manifold.cylinder(40, 2.2, 2.2, 48).rotate((0, 90, 0)).translate((-20, y, z)))
    cuts.append(ycyl(Y_HUB_MAG - 1, Y_HUB_MAG + MAG_H, MAG_D / 2))
    cuts.append(Manifold.cylinder(14, 2.6, 2.6, 48).rotate((-90, 0, 0)).translate((-21.5, -7, Z_J2 + 37)))
    for i in range(4):
        t = math.radians(45 + 90 * i)
        cuts.append(ycyl(Y_HUB_PULLEY - 9, Y_HUB_PULLEY + 1, 1.7, PULLEY_BOLT_PCD / 2 * math.cos(t), Z_J2 + PULLEY_BOLT_PCD / 2 * math.sin(t)))
    for c in cuts:
        body -= c
    return body


def big_pulley():
    wheel = ycyl(Y_PULLEY, Y_PULLEY + PULLEY_H, PD_BIG / 2 - 0.25)
    grooves = []
    for i in range(TEETH_BIG):
        t = 2 * math.pi * i / TEETH_BIG
        r = PD_BIG / 2 - 0.25
        grooves.append(ycyl(Y_PULLEY - 0.1, Y_PULLEY + PULLEY_H + 0.1, 0.6, r * math.cos(t), Z_J2 + r * math.sin(t)))
    wheel -= Manifold.compose(grooves)
    body = wheel + ycyl(Y_PULLEY + PULLEY_H, Y_PULLEY + PULLEY_H + 1.5, FLANGE_R)
    body += ycyl(Y_PULLEY - 1.5, Y_PULLEY, FLANGE_R)
    body += ycyl(TOWER_OUT + 0.05, Y_PULLEY, 20)
    for i in range(4):
        t = math.radians(45 + 90 * i)
        x, z = PULLEY_BOLT_PCD / 2 * math.cos(t), Z_J2 + PULLEY_BOLT_PCD / 2 * math.sin(t)
        body -= ycyl(TOWER_OUT, Y_PULLEY + PULLEY_H + 2, 1.8, x, z)
        body -= ycyl(Y_PULLEY + 8, Y_PULLEY + PULLEY_H + 2, 3.2, x, z)
    return body


def dummy_motor():
    gbox = ycyl(Y_FACE - GBOX_L, Y_FACE, GBOX_D / 2, X_MOTOR, Z_MOTOR)
    y0 = Y_FACE - GBOX_L - MOTOR_L
    can = box(X_MOTOR - MOTOR_W / 2, X_MOTOR + MOTOR_W / 2, y0, Y_FACE - GBOX_L, Z_MOTOR - MOTOR_W / 2, Z_MOTOR + MOTOR_W / 2)
    shaft = ycyl(Y_FACE + WALL_T + 0.1, Y_FACE + SHAFT_L, 4, X_MOTOR, Z_MOTOR)
    pulley = ycyl(Y_PULLEY, Y_PULLEY + PULLEY_H, PD_MOTOR / 2, X_MOTOR, Z_MOTOR)
    return gbox + can + shaft + pulley


def dummy_extrusion():
    """Upper arm spine, for the swing check."""
    a = box(-10, 10, SOCKET_Y - 10, SOCKET_Y + 10, Z_ROOT_TOP - SOCKET_DEPTH, Z_J2 + 221)
    b = box(-10, 10, -SOCKET_Y - 10, -SOCKET_Y + 10, Z_ROOT_TOP - SOCKET_DEPTH, Z_J2 + 221)
    return a + b


def swing(m, deg):
    return m.translate((0, 0, -Z_J2)).rotate((0, deg, 0)).translate((0, 0, Z_J2))


def main():
    parts = {'j2_housing': housing(), 'j2_arm_root': arm_root(), 'j2_pulley': big_pulley()}
    rot = rotor()
    motor = dummy_motor()
    print('Parts:')
    for name, m in parts.items():
        lo, hi = m.bounding_box()[:3], m.bounding_box()[3:]
        tm = to_trimesh(m)
        tm.merge_vertices()
        assert tm.is_watertight, name
        assert len(m.decompose()) == 1, f'{name} is not one piece'
        tm.export(OUT / f'{name}.stl')
        print(f'  {name:12} {[round(b - a, 1) for a, b in zip(lo, hi)]} mm, about {m.volume() / 1000 * 1.27 * 0.6:.0f} g')
    to_trimesh(rot).export(OUT / 'j1_rotor.stl')

    bad = 0

    def check(na, a, nb, b):
        nonlocal bad
        v = (a ^ b).volume()
        print(f'  {na:14} vs {nb:14}: {v:8.2f} mm3 {"OK" if v < 1 else "COLLISION"}')
        bad += v >= 1

    print('Static:')
    h, r, p = parts['j2_housing'], parts['j2_arm_root'], parts['j2_pulley']
    check('housing', h, 'turntable', rot)
    check('housing', h, 'motor', motor - ycyl(Y_FACE - 1, Y_FACE + WALL_T + 1, 13, X_MOTOR, Z_MOTOR))
    check('pulley', p, 'turntable', rot)
    check('pulley', p, 'housing', h)
    check('pulley', p, 'motor', motor)
    check('motor', motor, 'turntable', rot)
    print('Swing, J2 -35 to +90 deg:')
    arm = r + p + dummy_extrusion()
    worst = {}
    for deg in range(-35, 91, 5):
        moved = swing(arm, deg)
        for n, m in (('housing', h), ('turntable', rot), ('motor', motor)):
            worst[n] = max(worst.get(n, 0), (moved ^ m).volume())
    for n, v in worst.items():
        print(f'  arm vs {n:10}: {v:8.2f} mm3 {"OK" if v < 1 else "COLLISION"}')
        bad += v >= 1
    print(f'  belt centre distance {CENTRE:.2f} mm, motor at x {X_MOTOR:.1f}, z {Z_MOTOR:.1f}')
    print('ALL CHECKS PASSED' if not bad else f'{bad} PROBLEMS')


if __name__ == '__main__':
    main()
