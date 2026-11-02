"""Build the browser 3D model of the arm. Run: python build_viewer.py

Writes ../viewer/index.html. Host it with:
    cd ../viewer && python -m http.server 8766 --bind <address>
"""
import base64
import json
from pathlib import Path

import numpy as np
from manifold3d import Manifold

import base_j1 as b
import gripper as g
import j2_shoulder as j2
import j3_elbow as j3

OUT = Path(__file__).resolve().parent.parent / 'viewer'
PAGE = Path(__file__).with_name('viewer_template.html')


def tool(m):
    """Place a gripper part on the end of the arm. Tool Z becomes arm +X."""
    return m.rotate((0, 90, 0)).rotate((90, 0, 0)).translate((270, 0, j3.Z_E))


def placeholders():
    forearm = Manifold.cylinder(155, 25, 22, 64).rotate((0, 90, 0)).translate((60, -11, j3.Z_E))
    wrist = Manifold.cylinder(55, 22, 22, 64).rotate((0, 90, 0)).translate((215, 0, j3.Z_E))
    return forearm, wrist


def main():
    forearm, wrist = placeholders()
    z_f = g.Z_GEAR + g.GEAR_T + 9
    fingers = g.finger().translate((4.2 + 15, 0, z_f)) + g.finger().rotate((0, 0, 180)).translate((-4.2 - 15, 0, z_f))
    # name, mesh, colour, stage (0 base, 1 J1, 2 J2, 3 J3), kind
    parts = [
        ('Base shell', b.base_shell(), '#C9D2DB', 0, 'printed'),
        ('Deck and hub', b.deck(), '#8FA3B5', 0, 'printed'),
        ('Belt cover', b.belt_cover(), '#EEF2F6', 0, 'printed'),
        ('J1 motor', b.dummy_motor(), '#30393F', 0, 'buy'),
        ('J1 motor plate', b.motor_plate(), '#D9580B', 0, 'printed'),
        ('Bearing cap', b.bearing_cap(), '#30393F', 0, 'printed'),
        ('J1 turntable', b.rotor(), '#1F6FEB', 1, 'printed'),
        ('J2 housing', j2.housing(), '#8FA3B5', 1, 'printed'),
        ('J2 motor', j2.dummy_motor(), '#30393F', 1, 'buy'),
        ('J2 arm root', j2.arm_root(), '#EEF2F6', 2, 'printed'),
        ('J2 pulley', j2.big_pulley(), '#D9580B', 2, 'printed'),
        ('Upper arm', j3.upper_arm(), '#EEF2F6', 2, 'printed'),
        ('Tunnel lid', j3.lid(), '#B9C6D2', 2, 'printed'),
        ('J3 motor', j3.dummy_j3_motor(), '#30393F', 2, 'buy'),
        ('Elbow stem', j3.elbow_stem(), '#1F6FEB', 3, 'printed'),
        ('Elbow pulley', j3.elbow_pulley(), '#D9580B', 3, 'printed'),
        ('Forearm', forearm, '#DDE4EA', 3, 'placeholder'),
        ('Wrist', wrist, '#C9D2DB', 3, 'placeholder'),
        ('Gripper body', tool(g.body()), '#8FA3B5', 3, 'printed'),
        ('Gripper racks', tool(g.rack(1).translate((15, 0, 0)) + g.rack(-1).translate((-15, 0, 0))), '#D9580B', 3, 'printed'),
        ('Gripper fingers', tool(fingers), '#30393F', 3, 'printed'),
    ]
    data = []
    for name, m, colour, stage, kind in parts:
        mesh = m.to_mesh()
        v = np.asarray(mesh.vert_properties)[:, :3].astype('f4')
        f = np.asarray(mesh.tri_verts).astype('u4')
        data.append(dict(name=name, color=colour, stage=stage, kind=kind,
                         v=base64.b64encode(v.tobytes()).decode(), f=base64.b64encode(f.tobytes()).decode()))
    OUT.mkdir(exist_ok=True)
    html = PAGE.read_text(encoding='utf8').replace('/*DATA*/', json.dumps(data))
    (OUT / 'index.html').write_text(html, encoding='utf8')
    print(f'{len(html) // 1024} KB, {len(data)} parts')


if __name__ == '__main__':
    main()
