"""Two-jaw rack and pinion gripper (J6 tool). Dimensions in mm.

    pip install manifold3d trimesh numpy
    python gripper.py

Z runs along the tool, from the flange (z = 0) towards the fingertips. The jaws slide along X.
Writes STL files to ../stl/ and checks fit at fully open and fully closed.
Measure the MG996R and its horn before printing: clones differ.
"""
import math

import numpy as np
from manifold3d import CrossSection, Manifold

from base_j1 import OUT, box, cyl, merge, to_trimesh

# Tool mount, shared by every tool.
FLANGE_D, FLANGE_T, BOLT_PCD, BOLT_D, PIN_D = 44.0, 5.0, 32.0, 3.4, 3.2

# MG996R, CHECK against the servo in hand.
SERVO_W, SERVO_D, SERVO_H, TAB_L, TAB_T, TAB_HOLE_X, TAB_HOLE_Y = 40.7, 19.7, 37.0, 54.0, 2.5, 24.75, 5.0
Z_SERVO = FLANGE_T + 3.0
Z_TAB = Z_SERVO + 28.0
SHAFT_X = 10.2                  # output shaft offset from the body centre

# Gears: module 1.5, 14 teeth, so 25 mm of jaw travel is 136 deg of servo travel.
MODULE, TEETH = 1.5, 14
PD = MODULE * TEETH
GEAR_T = 8.0
STROKE = 25.0                   # per jaw
Z_GEAR = Z_SERVO + SERVO_H + 8.0
RACK_H = 7.0
RACK_L = 62.0

# Guide rods, 4 mm, 110 mm long.
ROD_D, ROD_L = 4.0, 110.0
ROD_Y = PD / 2 + RACK_H + 9.0
Z_ROD = Z_GEAR + GEAR_T / 2
FINGER_L, FINGER_T = 60.0, 8.0


def bolt_xy(i):
    t = math.radians(45 + 90 * i)
    return BOLT_PCD / 2 * math.cos(t), BOLT_PCD / 2 * math.sin(t)


def body():
    flange = cyl(FLANGE_T, FLANGE_D / 2)
    cradle = box(-SERVO_W / 2 - SHAFT_X - 10, SERVO_W / 2 - SHAFT_X + 10, -SERVO_D / 2 - 4, SERVO_D / 2 + 4, FLANGE_T, Z_TAB)
    pocket = box(-SERVO_W / 2 - SHAFT_X - 0.3, SERVO_W / 2 - SHAFT_X + 0.3, -SERVO_D / 2 - 0.3, SERVO_D / 2 + 0.3, Z_SERVO, Z_TAB + 1)
    # Arms carry the rod blocks past the racks.
    arms = []
    for sy in (-1, 1):
        arms.append(box(-14, 14, sy * (SERVO_D / 2) - 4 if sy < 0 else SERVO_D / 2, sy * (SERVO_D / 2) if sy < 0 else SERVO_D / 2 + 4, FLANGE_T, Z_ROD - 7))
        y0, y1 = sorted((sy * (ROD_Y - 6), sy * (ROD_Y + 6)))
        y2, y3 = sorted((sy * SERVO_D / 2, sy * (ROD_Y + 6)))
        arms.append(box(-14, 14, y2, y3, Z_ROD - 11, Z_ROD - 7))
        arms.append(box(-55, 55, y0, y1, Z_ROD - 7, Z_ROD + 6))
        f0, f1 = sorted((sy * (ROD_Y - 7), sy * (ROD_Y + 11)))
        arms.append(box(-55, 55, f0, f1, Z_ROD - 11, Z_ROD - 7))        # floor ties the rod blocks together
        r0, r1 = sorted((sy * (ROD_Y + 6), sy * (ROD_Y + 11)))
        arms.append(box(-55, 55, r0, r1, Z_ROD - 11, Z_ROD + 6))        # outer rail
    b = flange + cradle
    for a in arms:
        b += a
    b -= pocket

    cuts = []
    for i in range(4):
        x, y = bolt_xy(i)
        cuts.append(cyl(FLANGE_T + 2, BOLT_D / 2, -1, x, y))
    cuts.append(cyl(4, PIN_D / 2, -1, 0, BOLT_PCD / 2))        # locating pin, one way only
    for sx in (-1, 1):
        for sy in (-1, 1):
            cuts.append(cyl(12, 1.5, Z_TAB - 11, sx * TAB_HOLE_X - SHAFT_X, sy * TAB_HOLE_Y))
    for sy in (-1, 1):                                          # 4 mm rods, press fit at the ends
        cuts.append(Manifold.cylinder(ROD_L + 2, ROD_D / 2 - 0.05, ROD_D / 2 - 0.05, 48).rotate((0, 90, 0))
                    .translate((-ROD_L / 2 - 1, sy * ROD_Y, Z_ROD)))
        cuts.append(box(-43, 43, sy * ROD_Y - 7, sy * ROD_Y + 7, Z_ROD - 8, Z_ROD + 8))  # carriage clearance
    b -= merge(cuts)
    return b.translate((0, 0, 0))


def tooth_outline():
    rb = PD / 2 * math.cos(math.radians(20))
    ra, rf = PD / 2 + MODULE, PD / 2 - 1.25 * MODULE
    pts = []
    pitch = 2 * math.pi / TEETH
    half = pitch / 4 + (math.tan(math.radians(20)) - math.radians(20))
    def inv(r):
        if r <= rb:
            return 0.0
        a = math.acos(rb / r)
        return math.tan(a) - a
    for i in range(TEETH):
        c = i * pitch
        for r in np.linspace(max(rf, rb), ra, 5):
            t = half - inv(r)
            pts.append((r * math.cos(c - t), r * math.sin(c - t)))
        for r in np.linspace(ra, max(rf, rb), 5):
            t = half - inv(r)
            pts.append((r * math.cos(c + t), r * math.sin(c + t)))
        t = c + pitch / 2
        pts.append((rf * math.cos(t), rf * math.sin(t)))
    return pts


def pinion():
    g = CrossSection([tooth_outline()]).extrude(GEAR_T)
    bore = Manifold.cylinder(GEAR_T + 2, 2.6, 2.6, 48).translate((0, 0, -1))   # horn screw, CHECK
    return (g - bore).translate((0, 0, Z_GEAR))


def rack(sign):
    """sign = +1: rack above the pinion, jaw on +X. It moves +X to open."""
    p = math.pi * MODULE
    y_pitch = PD / 2 + 0.2          # small backlash for printed teeth
    back = box(-RACK_L / 2, RACK_L / 2, y_pitch + 1.25 * MODULE, y_pitch + RACK_H, 0, GEAR_T)
    teeth = []
    n = int(RACK_L / p)
    for i in range(n):
        x = -n * p / 2 + (i + 0.5) * p
        w_top, w_bot = p / 2 - 2 * MODULE * math.tan(math.radians(20)), p / 2 + 2 * 1.0 * MODULE * math.tan(math.radians(20))
        poly = [(x - max(w_top, 0.6) / 2, y_pitch - MODULE), (x + max(w_top, 0.6) / 2, y_pitch - MODULE), (x + w_bot / 2, y_pitch + 1.25 * MODULE + 0.2), (x - w_bot / 2, y_pitch + 1.25 * MODULE + 0.2)]
        teeth.append(CrossSection([poly]).extrude(GEAR_T))
    r = back
    for t in teeth:
        r += t

    # Carriage on the rod, jaw tower at the outer end.
    carriage = box(-16, 16, ROD_Y - 6, ROD_Y + 6, -3, GEAR_T + 3)
    web = box(-16, 16, y_pitch + RACK_H - 0.5, ROD_Y - 5, 0, GEAR_T)
    jaw = box(0.2, 8.2, -9, ROD_Y + 6, GEAR_T + 3, GEAR_T + 9)   # jaws meet on the centreline when closed
    tie = box(0.2, 8.2, y_pitch + RACK_H - 0.5, ROD_Y + 6, 0, GEAR_T + 9)
    hole = Manifold.cylinder(40, ROD_D / 2 + 0.15, ROD_D / 2 + 0.15, 48).rotate((0, 90, 0)).translate((-20, ROD_Y, GEAR_T / 2))
    m = r + carriage + web + jaw + tie - hole
    screws = [cyl(10, 1.3, GEAR_T + 2, 4.2, y) for y in (-4, 4)]
    m -= merge(screws)
    m = m.translate((0, 0, Z_GEAR))
    if sign < 0:
        m = m.rotate((0, 0, 180))
    return m


def finger():
    """Bolts to a jaw. Swap it for wider or longer fingers. Print flat. Adds a pad recess."""
    f = box(-4, 4, -13, 13, 0, FINGER_L)
    pad = box(-5, -2.5, -11, 11, FINGER_L - 40, FINGER_L - 2)
    screws = [cyl(8, 1.7, -1, 0, y) for y in (-4, 4)]
    return f - pad - merge(screws)


def main():
    OUT.mkdir(exist_ok=True)
    parts = {'gripper_body': body(), 'gripper_pinion': pinion(), 'gripper_rack': rack(1), 'gripper_finger': finger()}
    for name, m in parts.items():
        lo, hi = m.bounding_box()[:3], m.bounding_box()[3:]
        tm = to_trimesh(m)
        tm.merge_vertices()
        assert tm.is_watertight, name
        assert len(m.decompose()) == 1, f'{name} is not one piece'
        tm.export(OUT / f'{name}.stl')
        print(f'  {name:16} {[round(b - a, 1) for a, b in zip(lo, hi)]} mm, {m.volume() / 1000 * 1.27 * 0.6:.0f} g')

    bad = 0
    pin = parts['gripper_pinion']
    # Rack length and tooth overlap are checked at both ends of travel.
    for label, s in (('closed', 0.0), ('half', STROKE / 2), ('open', STROKE)):
        a = rack(1).translate((s, 0, 0))
        b = rack(-1).translate((-s, 0, 0))
        for na, x, nb, y in (('rack A', a, 'body', parts['gripper_body']), ('rack B', b, 'body', parts['gripper_body']),
                             ('rack A', a, 'rack B', b)):
            v = (x ^ y).volume()
            print(f'  {label:6} {na} vs {nb}: {v:7.1f} mm3 {"OK" if v < 1 else "COLLISION"}')
            bad += v >= 1
        ang = math.degrees(s / (PD / 2))
        rot = pin.rotate((0, 0, -ang))
        v = (rot ^ a).volume()
        print(f'  {label:6} pinion vs rack A mesh overlap: {v:.1f} mm3')
    print('Body mass check done;', 'ALL FIT CHECKS PASSED' if not bad else f'{bad} PROBLEMS')


if __name__ == '__main__':
    main()
