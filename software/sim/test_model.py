"""Headless checks for roboarm.xml. Run: python test_model.py"""
import math
from pathlib import Path

import mujoco
import numpy as np

XML = Path(__file__).with_name('roboarm.xml')
JOINTS = ['j1', 'j2', 'j3', 'j4', 'j5']


def setup():
    m = mujoco.MjModel.from_xml_path(str(XML))
    return m, mujoco.MjData(m)


def go(m, d, deg, grip=0.025, seconds=2.0):
    """Move to joint angles (degrees) with limited slew, like the real arm."""
    start = d.ctrl[:6].copy()
    goal = np.array([math.radians(a) for a in deg] + [grip])
    n = int(seconds / m.opt.timestep)
    for i in range(n):
        s = min(1, (i + 1) / (0.8 * n))
        d.ctrl[:6] = start + (goal - start) * s
        mujoco.mj_step(m, d)


def angles(m, d):
    return [round(math.degrees(d.joint(j).qpos[0]), 1) for j in JOINTS]


def main():
    m, d = setup()
    print(f'bodies {m.nbody}, joints {m.njnt}, actuators {m.nu}, arm mass '
          f'{sum(m.body_mass[m.body(n).id] for n in ("j1_turntable","j2_upper_arm","j3_forearm","j4_wrist","j5_tool","j6_finger_a","j6_finger_b")):.2f} kg')

    d.ctrl[1] = math.radians(15); d.ctrl[5] = 0.025
    for _ in range(1500):
        mujoco.mj_step(m, d)
    print('home holds:', angles(m, d))

    go(m, d, [0, 85, -80, -5, 0], seconds=5)
    for _ in range(1000):
        mujoco.mj_step(m, d)
    print('stretched out:', angles(m, d), 'torques',
          [round(float(x), 2) for x in d.actuator_force[:5]], 'tool x', round(float(d.site('tool').xpos[0]), 3))

    m, d = setup()
    d.ctrl[1] = math.radians(15); d.ctrl[5] = 0.025
    for _ in range(500):
        mujoco.mj_step(m, d)
    # Search the J2/J3/J4 pose that puts the tool over the red cube pointing down.
    cube = d.body('red_cube').xpos.copy()
    best = None
    for j2 in range(20, 91, 2):
        for j3 in range(-40, 81, 2):
            j4 = 90 - j2 - j3
            if not -110 <= j4 <= 110:
                continue
            a2, a3 = math.radians(j2), math.radians(j2 + j3)
            x = 0.221 * math.sin(a2) + 0.215 * math.cos(a3)
            z = 0.166 + 0.221 * math.cos(a2) - 0.215 * math.sin(a3)
            e = abs(x - cube[0])
            if abs(z - 0.145) < 0.004 and (best is None or e < best[0]):
                best = (e, j2, j3, j4)
    _, j2, j3, j4 = best
    print('grasp pose', j2, j3, j4, 'x error', round(best[0], 4))
    go(m, d, [0, j2 - 12, j3, j4 + 12, 0], seconds=3)
    go(m, d, [0, j2, j3, j4, 0], seconds=2)
    print('at cube: tool', np.round(d.site('tool').xpos, 3), 'cube', np.round(d.body('red_cube').xpos, 3))
    go(m, d, [0, j2, j3, j4, 0], grip=0.0, seconds=1.5)
    go(m, d, [0, 30, 0, 60, 0], grip=0.0, seconds=3)
    z = float(d.body('red_cube').xpos[2])
    print(f'lifted cube to z = {z:.3f} m', 'PICK OK' if z > 0.08 else 'PICK FAILED')


if __name__ == '__main__':
    main()
