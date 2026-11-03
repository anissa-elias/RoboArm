"""Lay every printable part flat for slicing. Run: python prepare_print.py

Reads ../stl/ (parts in arm position), rotates each into its print orientation, sits it on
z = 0, centres it, checks it fits a 256 x 256 x 260 mm build volume, and writes ../print/.
"""
from pathlib import Path

import numpy as np
import trimesh

HERE = Path(__file__).resolve().parent.parent
BUILD = (256.0, 256.0, 260.0)
SETTLE = set()
FLIP = ((180, 0, 0),)
AXIS_UP = ((90, 0, 0),)       # part axis along Y stands upright
NOSE_UP = ((0, -90, 0),)      # +X becomes up
# file: (rotations about X, Y, Z in degrees, copies to print)
PARTS = {
    'base_mount_plate': ((), 1), 'base_shell': ((), 1), 'base_deck': ((), 1),
    'j1_motor_plate': (FLIP, 1), 'j1_rotor': (FLIP, 1), 'j1_bearing_cap': ((), 1), 'j1_belt_cover': (FLIP, 1),
    'j2_housing': ((), 1), 'j2_arm_root': (AXIS_UP, 1), 'j2_pulley': (AXIS_UP, 1),
    'j3_upper_arm': (NOSE_UP, 1), 'j3_arm_lid': (((0, 90, 0),), 1), 'j3_elbow_stem': (AXIS_UP, 1), 'j3_elbow_pulley': (AXIS_UP, 1),
    'j4_forearm': (FLIP, 1), 'j4_forearm_lid': ((), 1), 'j4_compound_pulley': (AXIS_UP, 1), 'j4_wrist_pulley': (AXIS_UP, 1), 'j4_wrist_link': (AXIS_UP, 1),
    'j5_housing': (NOSE_UP, 1), 'j5_spindle': (NOSE_UP, 1), 'j5_tool_flange': (NOSE_UP, 1),
    'gripper_body': ((), 1), 'gripper_pinion': ((), 1), 'gripper_rack': ((), 2), 'gripper_finger': (((0, 90, 0),), 2),
}


def main():
    out = HERE / 'print'
    out.mkdir(exist_ok=True)
    bad = 0
    total = 0.0
    print(f'{"Part":22} {"Size on bed (mm)":22} {"Qty":3} {"Flat mm2":>8} {"Hang %":>6}')
    for name, (turns, qty) in PARTS.items():
        m = trimesh.load(HERE / 'stl' / f'{name}.stl')
        for rx, ry, rz in turns:
            m.apply_transform(trimesh.transformations.euler_matrix(*np.radians((rx, ry, rz))))
        if name in SETTLE:
            # The outer face tapers slightly, so tilt the biggest near-down face flat onto the bed.
            down = [i for i, f in enumerate(m.facets_normal) if f[2] < -0.9]
            best = max(down, key=lambda i: m.facets_area[i])
            normal = m.facets_normal[best]
            m.apply_transform(trimesh.geometry.align_vectors(normal, (0, 0, -1)))
        lo, hi = m.bounds
        m.apply_translation((-(lo[0] + hi[0]) / 2, -(lo[1] + hi[1]) / 2, -lo[2]))
        size = m.extents
        fits = all(s <= b for s, b in zip(size, BUILD))
        # Area touching the bed, and share of area overhanging more than 45 degrees (rough support guide).
        z = m.triangles_center[:, 2]
        n = m.face_normals[:, 2]
        flat = m.area_faces[(z < 0.2) & (n < -0.98)].sum()
        hang = m.area_faces[(n < -0.707) & (z > 0.3)].sum() / m.area * 100
        vol_ok = m.is_watertight and m.volume > 0
        print(f'{name:22} {" x ".join(f"{s:.0f}" for s in size):22} {qty:3} {flat:8.0f} {hang:6.1f}{"" if fits and vol_ok else "  PROBLEM"}')
        bad += not (fits and vol_ok and flat > 50)
        total += m.volume * qty
        m.export(out / f'{name}.stl')
    print(f'Total {total / 1000:.0f} cm3 solid, about {total / 1000 * 1.27 * 0.6:.0f} g of PETG at 60% effective fill')
    print('ALL PARTS FIT AND SIT FLAT' if not bad else f'{bad} PROBLEMS')


if __name__ == '__main__':
    main()
