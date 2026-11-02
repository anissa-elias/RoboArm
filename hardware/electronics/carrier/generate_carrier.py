"""Soldering plan for the driver carrier, on a 7 x 9 cm perfboard (24 x 30 holes, 2.54 mm).

    python generate_carrier.py [path to output/arm.net]

Reads the KiCad netlist, places every part on the hole grid, joins holes on the same net with
wires, and checks each joint against the netlist. Writes the layout PDF, wire list and connector
pinouts. Change the placement here, never by hand in the output files.

Holes are named by column letter A-X and row number 1-30, seen from the component side.
"""
import csv
import re
import sys
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Rectangle

HERE = Path(__file__).parent
COLS, ROWS = 24, 30
NET = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE.parent / 'output' / 'arm.net'
JOINT = ['J1', 'J2', 'J3', 'J4', 'J5']


def read_nets():
    text = NET.read_text(encoding='utf8')
    pin = {}
    for m in re.finditer(r'\(net \(code "?\d+"?\) \(name "([^"]*)"\)(.*?)\)\s*(?=\(net |\)\s*\)\s*$)', text, re.S):
        for ref, p in re.findall(r'\(node \(ref "([^"]+)"\) \(pin "([^"]+)"\)', m.group(2)):
            pin[(ref, p)] = m.group(1)
    return pin


NETS = read_nets()
holes = {}      # (col, row) -> (label, net)
parts = []      # drawing: (kind, col0, row0, col1, row1, label, colour)


def name(c, r):
    return f'{chr(65 + c)}{r + 1}'


def put(c, r, label, ref_pin):
    """Claim a hole for a schematic pin. Two parts can never share a hole."""
    assert 0 <= c < COLS and 0 <= r < ROWS, (c, r, label)
    assert (c, r) not in holes, f'{label} clashes with {holes.get((c, r))} at {name(c, r)}'
    net = NETS[ref_pin]
    holes[(c, r)] = (label, net)
    return net


# ---- drivers, pin 1-8 down the left, then VM to GND down the right, with the motor plug beside them
DRV_POS = [(0, 1), (7, 1), (14, 1), (0, 12), (7, 12)]
LEFT = ['1', '2', '3', '4', '5', '6', '7', '8']           # EN MS1 MS2 UART UART CLK STEP DIR
RIGHT = ['16', '15', '14', '13', '12', '11', '10', '9']   # VM GND A2 A1 B1 B2 VCC_IO GND
LEFT_NAME = ['EN', 'MS1', 'MS2', 'UART', 'UART2', 'CLK', 'STEP', 'DIR']
RIGHT_NAME = ['VM', 'GND', 'A2', 'A1', 'B1', 'B2', 'VIO', 'GND']
for i, (c, r) in enumerate(DRV_POS):
    ref = f'DRV{i + 1}'
    for k, p in enumerate(LEFT):
        if ('%s' % ref, p) in NETS and k != 4:
            put(c, r + k, f'{ref} {LEFT_NAME[k]}', (ref, p))
        elif k == 4:
            holes[(c, r + k)] = (f'{ref} {LEFT_NAME[k]}', None)   # socket pin, left unconnected
    for k, p in enumerate(RIGHT):
        put(c + 5, r + k, f'{ref} {RIGHT_NAME[k]}', (ref, p))
    parts.append(('driver', c, r, c + 5, r + 7, f'{ref}\n{JOINT[i]}', '#F2E6C9'))
    for k, (p, nm) in enumerate(zip(RIGHT[2:6], ('A2', 'A1', 'B1', 'B2'))):
        put(c + 6, r + 2 + k, f'M{i + 1} plug {nm}', (ref, p))
    parts.append(('plug', c + 6, r + 2, c + 6, r + 5, f'M{i + 1}', '#CFE0F7'))
    # 100 uF across VM, under the driver's power pins. Long leg (+) towards VM.
    rr = r + 8
    put(c + 3, rr, f'C{20 + i} +', (f'C{20 + i}', '1'))
    put(c + 5, rr, f'C{20 + i} -', (f'C{20 + i}', '2'))
    parts.append(('cap', c + 3, rr, c + 5, rr, f'C{20 + i}', '#D7EAD3'))
    # EN pull-up
    put(c, rr + 1, f'R{21 + i} EN', (f'R{21 + i}', '2'))
    put(c + 4, rr + 1, f'R{21 + i} 5V', (f'R{21 + i}', '1'))
    parts.append(('res', c, rr + 1, c + 4, rr + 1, f'R{21 + i} 10k', '#EAD7D7'))

# ---- encoder filters, in the free driver slot
for i in range(5):
    row = 12 + i * 2
    put(14, row, f'R{1 + i} A{i}', (f'R{1 + i}', '1'))
    put(18, row, f'R{1 + i} ENC', (f'R{1 + i}', '2'))
    parts.append(('res', 14, row, 18, row, f'R{1 + i} 1k', '#EAD7D7'))
    put(14, row + 1, f'C{1 + i} A{i}', (f'C{1 + i}', '1'))
    put(16, row + 1, f'C{1 + i} GND', (f'C{1 + i}', '2'))
    parts.append(('cap', 14, row + 1, 16, row + 1, f'C{1 + i}', '#D7EAD3'))
# ---- series resistors
for k, (ref, a, b) in enumerate((('R31', '1', '2'), ('R32', '1', '2'), ('R13', '1', '2'))):
    row = 22 + k
    put(14, row, f'{ref} a', (ref, a))
    put(18, row, f'{ref} b', (ref, b))
    parts.append(('res', 14, row, 18, row, f'{ref} 1k', '#EAD7D7'))

# ---- encoder plugs: OUT, 5V, GND
for i in range(5):
    c = 19 + i
    put(c, 22, f'ENC{i + 1} OUT', (f'ENC{i + 1}', 'OUT'))
    put(c, 23, f'ENC{i + 1} 5V', (f'ENC{i + 1}', 'VCC'))
    put(c, 24, f'ENC{i + 1} GND', (f'ENC{i + 1}', 'GND'))
    parts.append(('plug', c, 22, c, 24, f'E{i + 1}', '#CFE0F7'))

# ---- power and other plugs
put(0, 24, '24 V in +', ('K1', '87'))
put(2, 24, '24 V in -', ('PS1', 'VN'))
parts.append(('term', 0, 24, 2, 24, '24 V IN', '#F7CFCF'))
put(4, 24, 'FAN +', ('FAN1', '1'))
put(5, 24, 'FAN -', ('FAN1', '2'))
parts.append(('plug', 4, 24, 5, 24, 'FAN', '#CFE0F7'))
put(7, 24, 'BUCK +', ('F1', '1'))
put(9, 24, 'BUCK -', ('U6', 'GI'))
parts.append(('term', 7, 24, 9, 24, 'TO F1 / U6', '#F7CFCF'))
put(11, 24, 'SERVO PWM', ('J6', '1'))
parts.append(('plug', 11, 24, 11, 24, 'PWM', '#CFE0F7'))

# ---- Mega plug, two rows along the bottom edge
MEGA = [f'D{22 + i}' for i in range(5)] + [f'D{30 + i}' for i in range(5)] + [f'D{36 + i}' for i in range(5)] + \
       ['D16', 'D17', 'D14', 'D15', 'D9'] + [f'A{i}' for i in range(5)] + ['P5V', 'DGND1']
mega_pos = []
for i, p in enumerate(MEGA):
    c, r = (i, 27) if i < 16 else (i - 16, 28)
    put(c, r, f'Mega {p}', ('U2', p))
    mega_pos.append((c, r, p))
parts.append(('plug', 0, 27, 15, 28, 'TO MEGA', '#CFE0F7'))

# ---- wires: within each net, chain holes along the shortest path
by_net = {}
for pos, (label, net) in holes.items():
    if net is not None:
        by_net.setdefault(net, []).append(pos)

wires = []
for net, pts in sorted(by_net.items()):
    left, done = set(pts[1:]), [pts[0]]
    while left:
        a, b = min(((p, q) for p in done for q in left), key=lambda t: abs(t[0][0] - t[1][0]) + abs(t[0][1] - t[1][1]))
        wires.append((net, a, b))
        done.append(b)
        left.remove(b)


def kind(net):
    return 'power' if net in ('+24V', 'GND', '+5V') else ('motor' if 'B' in net and False else 'signal')


def adjacent(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1]) == 1


def check():
    """Rebuild connectivity from the wires alone and compare it with the KiCad netlist."""
    parent = {p: p for p in holes}

    def find(p):
        while parent[p] != p:
            parent[p] = parent[parent[p]]
            p = parent[p]
        return p

    for _, a, b in wires:
        parent[find(a)] = find(b)
    bad = 0
    groups = {}
    for p, (label, net) in holes.items():
        if net is not None:
            groups.setdefault(find(p), set()).add(net)
    for g in groups.values():
        if len(g) != 1:
            print('SHORT between', g)
            bad += 1
    seen = {}
    for p, (label, net) in holes.items():
        if net is None:
            continue
        if net in seen and find(seen[net]) != find(p):
            print('OPEN on', net)
            bad += 1
        seen[net] = p
    # Every driver must keep its address, and every required board pin must exist on the board.
    need = [(f'DRV{i + 1}', p) for i in range(5) for p in ('1', '2', '3', '4', '6', '7', '8', '9', '10', '11', '12', '13', '14', '15', '16')]
    placed = {net for _, net in holes.values()}
    for rp in need:
        if NETS[rp] not in placed:
            print('MISSING', rp)
            bad += 1
    for i, (c, r) in enumerate(DRV_POS):
        a0, a1 = holes[(c, r + 1)][1], holes[(c, r + 2)][1]
        want = (i % 3 == 1, i % 3 == 2)
        if (a0 == '+5V', a1 == '+5V') != want:
            print('WRONG UART ADDRESS on', i + 1)
            bad += 1
    return bad


def draw():
    fig, ax = plt.subplots(figsize=(11.0, 15.0))
    ax.add_patch(Rectangle((-1.1, -1.1), COLS + 1.2, ROWS + 1.2, fc='#FBFAF5', ec='#333', lw=1.5))
    for p in parts:
        k, c0, r0, c1, r1, label, col = p
        ax.add_patch(Rectangle((c0 - .42, r0 - .42), c1 - c0 + .84, r1 - r0 + .84, fc=col, ec='#555', lw=.8, zorder=1))
        ax.text((c0 + c1) / 2, (r0 + r1) / 2, label, ha='center', va='center', fontsize=8 if k in ('driver',) else 5.6, zorder=5, weight='bold' if k == 'driver' else 'normal')
    for c in range(COLS):
        ax.text(c, -0.85, chr(65 + c), ha='center', fontsize=7, weight='bold')
    for r in range(ROWS):
        ax.text(-0.8, r, str(r + 1), va='center', ha='right', fontsize=7, weight='bold')
    colour = {'+24V': '#D00000', 'GND': '#111111', '+5V': '#E8590C'}
    for net, a, b in wires:
        if adjacent(a, b):
            ax.plot([a[0], b[0]], [a[1], b[1]], color=colour.get(net, '#2F6FBF'), lw=3.2, solid_capstyle='round', zorder=3)
        else:
            ax.plot([a[0], b[0]], [a[1], b[1]], color=colour.get(net, '#2F6FBF'), lw=1.5 if net in colour else .8, alpha=.75, zorder=3)
    for c in range(COLS):
        for r in range(ROWS):
            used = (c, r) in holes
            ax.add_patch(Circle((c, r), .15 if used else .08, fc='#222' if used else '#BBB', ec='none', zorder=4))
    ax.set_xlim(-2, COLS + .5)
    ax.set_ylim(ROWS + .6, -1.7)
    ax.set_aspect('equal')
    ax.axis('off')
    ax.set_title('RoboArm driver carrier, component side, 7 x 9 cm perfboard\n'
                 'Red 24 V, black ground, orange 5 V, blue signal. Wires run on the back. Short thick lines are solder bridges between neighbouring holes.\n'
                 'ORIENTATION: on every driver, EN is the top-left pin and VM is the top-right pin. A driver fitted backwards will be destroyed.', fontsize=10)
    fig.savefig(HERE / 'carrier_layout.pdf', bbox_inches='tight')
    fig.savefig(HERE / 'carrier_layout.png', dpi=110, bbox_inches='tight')


def write():
    rows = []
    gauge = {'+24V': '18 AWG', 'GND': '18 AWG', '+5V': '22 AWG'}
    for net, a, b in sorted(wires, key=lambda w: (w[0] not in ('+24V', 'GND', '+5V'), w[0], w[1])):
        d = abs(a[0] - b[0]) + abs(a[1] - b[1])
        rows.append((len(rows) + 1, name(*a), holes[a][0], name(*b), holes[b][0], net, 'solder bridge' if d == 1 else f'{gauge.get(net, "22 AWG")}, {d * 2.54 + 8:.0f} mm'))
    with open(HERE / 'wire_list.csv', 'w', newline='', encoding='utf8') as f:
        w = csv.writer(f)
        w.writerow(['#', 'From hole', 'From', 'To hole', 'To', 'Net', 'Wire'])
        w.writerows(rows)
    with open(HERE / 'mega_plug.csv', 'w', newline='', encoding='utf8') as f:
        w = csv.writer(f)
        w.writerow(['Hole', 'Mega pin', 'Function'])
        fn = {**{f'D{22 + i}': f'STEP {JOINT[i]}' for i in range(5)}, **{f'D{30 + i}': f'DIR {JOINT[i]}' for i in range(5)},
              **{f'D{36 + i}': f'EN {JOINT[i]}' for i in range(5)}, **{f'A{i}': f'Encoder {JOINT[i]}' for i in range(5)},
              'D16': 'UART A TX, J1-J3', 'D17': 'UART A RX', 'D14': 'UART B TX, J4-J5', 'D15': 'UART B RX', 'D9': 'Gripper PWM',
              'P5V': '5 V', 'DGND1': 'GND'}
        for c, r, p in mega_pos:
            w.writerow([name(c, r), {'P5V': '5V', 'DGND1': 'GND'}.get(p, p), fn[p]])
    return len(rows)


if __name__ == '__main__':
    bad = check()
    n = write()
    draw()
    print(f'{len(holes)} holes, {n} wires, {len(by_net)} nets')
    print('ALL CONNECTIONS MATCH THE NETLIST' if not bad else f'{bad} PROBLEMS')
    sys.exit(1 if bad else 0)
