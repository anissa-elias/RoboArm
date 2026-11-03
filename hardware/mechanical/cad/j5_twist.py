"""J5 wrist twist and the tool flange. All dimensions in mm, same frame as base_j1.py.

    pip install manifold3d trimesh numpy
    python j5_twist.py

Drawn at J3 = J4 = 0. The twist axis runs along +X through the wrist. The housing bolts to the
front of the J4 wrist link. Tools bolt to the flange at X_TOOL.
Writes STL files to ../stl/ and checks fit through the J4 and J5 travel, with the gripper fitted.
Measure before printing: anything marked CHECK came from a generic drawing.
"""
import math

from manifold3d import Manifold

from base_j1 import OUT, box, cyl, to_trimesh
from gripper import BOLT_PCD, BOLT_D, FLANGE_D, FLANGE_T, PIN_D, bolt_xy, body as g_body, finger, rack
from gripper import GEAR_T, Z_GEAR, STROKE
from j2_shoulder import ycyl
from j3_elbow import Z_E
from j4_forearm import X_W, centre_distance, hinge, _toothed, forearm, forearm_lid, dummy_motor as j4_motor, pd

X_LINK = X_W + 38.0           # front of the wrist link
X_BULK = X_LINK + 3.5         # bulkhead the motor bolts to
X_BAY = (X_BULK, X_BULK + 9.5)
X_BEAR = (X_BAY[1], X_BAY[1] + 12.0)
X_TOOL = X_BEAR[1] + 5.5      # tool face

# Bearings: 2 x 6803 (17 x 26 x 5).
B_ID, B_OD, B_W = 17.0, 26.0, 5.0
FIT = 0.15
BORE = 10.0                   # wires for the tool pass down the spindle

# Belt: 16T on the motor to 64T on the spindle, 4:1, 180 mm 6 mm GT2 loop.
T_S, T_B, BELT = 16, 64, 180.0
C = centre_distance(T_S, T_B, BELT)

# 11HS12-0674S, 31.5 mm NEMA 11. CHECK against the motor in hand.
MOTOR_W, MOTOR_L = 28.2, 31.5
MOTOR_HOLE, MOTOR_BOSS = 23.0, 22.5


def xcyl(x0, x1, r, y=0.0, z=Z_E):
    return Manifold.cylinder(x1 - x0, r, r, 96).rotate((0, 90, 0)).translate((x0, y, z))


def pod(r_low, r_high, x0, x1):
    """Stadium around the spindle and the motor shaft."""
    return Manifold.batch_hull([xcyl(x0, x1, r_low), xcyl(x0, x1, r_high, 0, Z_E + C)])


def housing():
    bulk = pod(24, 16, X_LINK, X_BULK)
    bay = pod(24, 16, X_BULK, X_BAY[1])
    nose = xcyl(X_BEAR[0], X_BEAR[1], 17) + Manifold.batch_hull([xcyl(X_BEAR[0], X_BEAR[0] + 4, 24), xcyl(X_BEAR[0] + 8, X_BEAR[1], 17)])
    front = pod(24, 16, X_BEAR[0] - 1.5, X_BEAR[0])
    body = bulk + bay + nose + front
    body -= pod(21.5, 13.5, X_BAY[0], X_BAY[1] - 1.5 + 0.01)
    body -= xcyl(X_BEAR[0] - 2, X_BEAR[0] + B_W, (B_OD + 2 * FIT) / 2)
    body -= xcyl(X_BEAR[1] - B_W, X_BEAR[1] + 1, (B_OD + 2 * FIT) / 2)
    body -= xcyl(X_BEAR[0] + B_W - 1, X_BEAR[1] - B_W + 1, 11)
    cuts = [xcyl(X_LINK - 1, X_BULK + 1, MOTOR_BOSS / 2 + 0.5, 0, Z_E + C)]   # motor boss, belt tension by shims
    for sy in (-1, 1):
        for sz in (-1, 1):
            cuts.append(xcyl(X_LINK - 1, X_BULK + 1, 1.45, sy * MOTOR_HOLE / 2, Z_E + C + sz * MOTOR_HOLE / 2))
    # Wires pass under the encoder, which sits in a window on the axis.
    cuts.append(box(X_LINK - 1, X_BULK + 1, -12.0, 12.0, Z_E - 15.0, Z_E + 12.0))
    for sy in (-6.0, 6.0):
        for z in (Z_E - 15.5, Z_E + 15.5):
            cuts.append(xcyl(X_LINK - 1, X_BULK + 1, 1.7, sy, z))
    for c in cuts:
        body -= c
    # Encoder ledges, either side of the window.
    return body


def spindle():
    wheel = _toothed(T_B, 0, 6.5, 0, 0)            # built along Y at the origin, then laid along X
    wheel = wheel.rotate((0, 0, -90)).translate((X_BAY[0] + 1.0, 0, Z_E))
    fl = xcyl(X_BAY[0] + 0.6, X_BAY[0] + 1.0, pd(T_B) / 2 + 1.0) + xcyl(X_BAY[0] + 7.5, X_BAY[0] + 8.0, pd(T_B) / 2 + 1.0)
    shoulder = xcyl(X_BAY[0] + 7.9, X_BEAR[0] + 0.3, 11)
    shaft = xcyl(X_BAY[0] + 1, X_BEAR[1] + 0.6, (B_ID - FIT) / 2)
    body = wheel + fl + shoulder + shaft
    body -= xcyl(X_BAY[0] - 1, X_BEAR[1] + 2, BORE / 2)
    spoke = box(X_BAY[0] + 0.6, X_BAY[0] + 2.6, -8.4, 8.4, Z_E - 1.6, Z_E + 1.6) + xcyl(X_BAY[0] + 0.6, X_BAY[0] + 2.6, 4.2)
    body += spoke
    body -= xcyl(X_BAY[0] + 0.5, X_BAY[0] + 2.0, 3.1)                            # magnet
    for i in range(3):
        t = math.radians(90 + 120 * i)
        body -= xcyl(X_BEAR[1] - 8, X_BEAR[1] + 1, 0.95, 6.8 * math.cos(t), Z_E + 6.8 * math.sin(t))
    return body


def tool_flange():
    """Every tool bolts to this. The tab carries the GX12 tool plug."""
    disc = xcyl(X_BEAR[1] + 0.7, X_TOOL, FLANGE_D / 2)
    tab = Manifold.batch_hull([xcyl(X_BEAR[1] + 0.7, X_TOOL, 12, 0, Z_E - 28), box(X_BEAR[1] + 0.7, X_TOOL, -12, 12, Z_E - 16, Z_E - 12)])
    body = disc + tab
    body -= xcyl(X_BEAR[1], X_TOOL + 1, BORE / 2)
    body -= box(X_BEAR[1], X_TOOL - 2, -3.5, 3.5, Z_E - 34, Z_E)                 # wire groove to the plug
    body -= Manifold.cylinder(12, 6.1, 6.1, 64).rotate((0, 90, 0)).translate((X_BEAR[1], 0, Z_E - 28))
    for i in range(4):
        y, z = bolt_xy(i)
        body -= xcyl(X_BEAR[1], X_TOOL + 1, 1.5, y, Z_E + z)
    body -= xcyl(X_TOOL - 3, X_TOOL + 1, PIN_D / 2, BOLT_PCD / 2 * 0, Z_E + BOLT_PCD / 2)
    for i in range(3):
        t = math.radians(90 + 120 * i)
        body -= xcyl(X_BEAR[1], X_TOOL + 1, 1.3, 6.8 * math.cos(t), Z_E + 6.8 * math.sin(t))
    return body


def dummy_motor():
    can = box(X_LINK - MOTOR_L, X_LINK, -MOTOR_W / 2, MOTOR_W / 2, Z_E + C - MOTOR_W / 2, Z_E + C + MOTOR_W / 2)
    shaft = xcyl(X_BULK + 0.1, X_BAY[1] - 2, 2.5, 0, Z_E + C)
    pulley = xcyl(X_BAY[0] + 1, X_BAY[0] + 7.5, pd(T_S) / 2 + 0.6, 0, Z_E + C)
    return can + shaft + pulley


def tool(m):
    """Place a part drawn in tool coordinates (Z along the tool) on the flange."""
    return m.rotate((0, 90, 0)).rotate((90, 0, 0)).translate((X_TOOL, 0, Z_E))


def gripper_parts(opening=30.0):
    s = opening / 2
    z = Z_GEAR + GEAR_T + 9
    fingers = finger().translate((4.2 + s, 0, z)) + finger().rotate((0, 0, 180)).translate((-4.2 - s, 0, z))
    return [tool(g_body()), tool(rack(1).translate((s, 0, 0)) + rack(-1).translate((-s, 0, 0))), tool(fingers)]


def twist(m, deg):
    return m.translate((0, 0, -Z_E)).rotate((deg, 0, 0)).translate((0, 0, Z_E))


def main():
    parts = {'j5_housing': housing(), 'j5_spindle': spindle(), 'j5_tool_flange': tool_flange()}
    print('Parts:')
    for name, m in parts.items():
        lo, hi = m.bounding_box()[:3], m.bounding_box()[3:]
        tm = to_trimesh(m)
        assert tm.is_watertight, name
        n = len(m.decompose())
        print(f'  {name:15} {[round(b - a, 1) for a, b in zip(lo, hi)]} mm, about {m.volume() / 1000 * 1.27 * 0.6:.0f} g, {n} piece(s)')
        if n > 1:
            print('   pieces:', [[round(v) for v in q.bounding_box()] for q in m.decompose()])
        assert n == 1, f'{name} is not one piece'
        tm.export(OUT / f'{name}.stl')
    h, sp, fl = parts['j5_housing'], parts['j5_spindle'], parts['j5_tool_flange']
    mot = dummy_motor()
    from j4_forearm import wrist_link, wrist_pulley
    link = wrist_link()
    grip = gripper_parts(50.0)
    bad = 0

    def check(na, a, nb, b):
        nonlocal bad
        v = (a ^ b).volume()
        print(f'  {na:12} vs {nb:12}: {v:8.2f} mm3 {"OK" if v < 1 else "COLLISION"}')
        bad += v >= 1

    print('Static:')
    check('housing', h, 'spindle', sp)
    check('housing', h, 'flange', fl)
    check('housing', h, 'link', link)
    check('housing', h, 'motor', mot - xcyl(X_LINK - 1, X_BULK + 1, 12, 0, Z_E + C))
    check('spindle', sp, 'motor', mot)
    check('spindle', sp, 'flange', fl)
    check('motor', mot, 'link', link)
    print('J5 travel, -145 to +145 deg, gripper fully open:')
    w = {}
    for d in range(-145, 146, 15):
        moved = [twist(g, d) for g in grip] + [twist(fl, d)]
        for n, m in (('housing', h), ('motor', mot)):
            w[n] = max([w.get(n, 0)] + [(g ^ m).volume() for g in moved])
    for n, v in w.items():
        print(f'  tool vs {n:8}: {v:8.2f} mm3 {"OK" if v < 1 else "COLLISION"}')
        bad += v >= 1
    print('J4 travel of the wrist, housing and motor, by angle:')
    fore = forearm() + forearm_lid() + j4_motor()
    pack = h + mot + twist(fl, 0)
    limits = []
    for d in range(-110, 111, 10):
        v = (hinge(pack, d) ^ fore).volume()
        print(f'  J4 {d:+5d}: {v:9.1f} mm3 {"OK" if v < 1 else "COLLISION"}')
        if v < 1:
            limits.append(d)
    print(f'  clear from {min(limits)} to {max(limits)}; tool face at x {X_TOOL:.1f}, {X_TOOL - X_W:.1f} mm past J4; belt centres {C:.1f} mm')
    print('ALL CHECKS PASSED' if not bad else f'{bad} PROBLEMS')


if __name__ == '__main__':
    main()
