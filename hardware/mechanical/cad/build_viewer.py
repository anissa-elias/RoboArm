"""Build the browser 3D model of the arm. Run: python build_viewer.py

Writes ../viewer/index.html. Host it with:
    cd ../viewer && python -m http.server 8766 --bind <address>
"""
import base64
import json
from pathlib import Path

import numpy as np

import base_j1 as b
import j2_shoulder as j2
import j3_elbow as j3
import j4_forearm as j4
import j5_twist as j5

OUT = Path(__file__).resolve().parent.parent / 'viewer'
PAGE = Path(__file__).with_name('viewer_template.html')


# One colour per joint, used everywhere the arm is drawn.
JOINTS = {'J1': '#1F6FEB', 'J2': '#0CA678', 'J3': '#E8590C', 'J4': '#7048E8', 'J5': '#D6336C', 'J6': '#F2B705'}


def main():
    grip = j5.gripper_parts(30.0)
    # name, mesh, colour, stage (0 base, 1 J1, 2 J2, 3 J3), kind
    n, dark = '#C9D2DB', '#30393F'     # neutral structure, motors
    parts = [
        ('Mounting plate', b.mount_plate(), '#7D8A96', 0, 'printed', 'Base'),
        ('Base shell', b.base_shell(), n, 0, 'printed', 'Base'),
        ('Deck', b.deck(), '#9AA8B5', 0, 'printed', 'Base'),
        ('Belt cover', b.belt_cover(), JOINTS['J1'], 0, 'printed', 'J1'),
        ('Motor', b.dummy_motor(), dark, 0, 'buy', 'J1'),
        ('Motor plate', b.motor_plate(), JOINTS['J1'], 0, 'printed', 'J1'),
        ('Bearing cap', b.bearing_cap(), JOINTS['J1'], 0, 'printed', 'J1'),
        ('Turntable', b.rotor(), JOINTS['J1'], 1, 'printed', 'J1'),
        ('Housing', j2.housing(), JOINTS['J2'], 1, 'printed', 'J2'),
        ('Motor', j2.dummy_motor(), dark, 1, 'buy', 'J2'),
        ('Arm root', j2.arm_root(), JOINTS['J2'], 2, 'printed', 'J2'),
        ('Pulley', j2.big_pulley(), JOINTS['J2'], 2, 'printed', 'J2'),
        ('Upper arm', j3.upper_arm(), '#EEF2F6', 2, 'printed', 'Arm'),
        ('Tunnel lid', j3.lid(), '#DDE4EA', 2, 'printed', 'Arm'),
        ('Motor', j3.dummy_j3_motor(), dark, 2, 'buy', 'J3'),
        ('Elbow stem', j3.elbow_stem(), JOINTS['J3'], 3, 'printed', 'J3'),
        ('Elbow pulley', j3.elbow_pulley(), JOINTS['J3'], 3, 'printed', 'J3'),
        ('Forearm', j4.forearm(), '#EEF2F6', 3, 'printed', 'Arm'),
        ('Forearm lid', j4.forearm_lid(), '#DDE4EA', 3, 'printed', 'Arm'),
        ('Motor', j4.dummy_motor(), dark, 3, 'buy', 'J4'),
        ('Compound pulley', j4.compound_pulley(), JOINTS['J4'], 3, 'printed', 'J4'),
        ('Wrist pulley', j4.wrist_pulley(), JOINTS['J4'], 4, 'printed', 'J4'),
        ('Wrist link', j4.wrist_link(), JOINTS['J4'], 4, 'printed', 'J4'),
        ('Housing', j5.housing(), JOINTS['J5'], 4, 'printed', 'J5'),
        ('Motor', j5.dummy_motor(), dark, 4, 'buy', 'J5'),
        ('Spindle', j5.spindle(), JOINTS['J5'], 5, 'printed', 'J5'),
        ('Tool flange', j5.tool_flange(), JOINTS['J5'], 5, 'printed', 'J5'),
        ('Gripper body', grip[0], JOINTS['J6'], 5, 'printed', 'J6'),
        ('Gripper racks', grip[1], JOINTS['J6'], 5, 'printed', 'J6'),
        ('Gripper fingers', grip[2], dark, 5, 'printed', 'J6'),
    ]
    data = []
    for name, m, colour, stage, kind, group in parts:
        mesh = m.to_mesh()
        v = np.asarray(mesh.vert_properties)[:, :3].astype('f4')
        f = np.asarray(mesh.tri_verts).astype('u4')
        data.append(dict(name=name, color=colour, stage=stage, kind=kind, group=group,
                         v=base64.b64encode(v.tobytes()).decode(), f=base64.b64encode(f.tobytes()).decode()))
    OUT.mkdir(exist_ok=True)
    html = PAGE.read_text(encoding='utf8').replace('/*DATA*/', json.dumps(data)).replace('/*JOINTS*/', json.dumps(JOINTS))
    (OUT / 'index.html').write_text(html, encoding='utf8')
    print(f'{len(html) // 1024} KB, {len(data)} parts')


if __name__ == '__main__':
    main()
