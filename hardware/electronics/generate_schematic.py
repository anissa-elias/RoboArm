"""RoboArm electronics schematic generator (rev C).

Builds custom_arm.kicad_sch: a single A1 sheet with every board pin shown and
parts joined by drawn wires.

Run:   python generate_schematic.py
Check: kicad-cli sch erc custom_arm.kicad_sch
       kicad-cli sch export netlist -o output/arm.net custom_arm.kicad_sch
       python verify_netlist.py output/arm.net

Set KICAD9_SYMBOL_DIR if KiCad's symbol libraries are not in the default
Windows install location.
"""
import json, uuid, math, csv, re, os
from pathlib import Path

P = Path(__file__).resolve().parent
KLIB = Path(os.environ.get('KICAD9_SYMBOL_DIR', r'C:\Program Files\KiCad\9.0\share\kicad\symbols'))
(P / 'output').mkdir(parents=True, exist_ok=True)

G = 1.27
def g(v): return round(round(v / G) * G, 2)
def uid(): return str(uuid.uuid4())
def q(s): return json.dumps(str(s))

ROOT = uid()
BODY_H = {}
items, libdefs, records = [], {}, []
counters = {}

# ---------------------------------------------------------------- symbols
def lib_block(lib, name):
    t = (KLIB / f'{lib}.kicad_sym').read_text(encoding='utf8')
    i = t.find(f'(symbol "{name}"')
    d = 0
    for j in range(i, len(t)):
        if t[j] == '(':
            d += 1
        elif t[j] == ')':
            d -= 1
            if d == 0:
                return t[i:j + 1]

PINRE = re.compile(r'\(pin (\w+) \w+\s*\(at ([-\d.]+) ([-\d.]+) (\d+)\)\s*\(length [\d.]+\).*?\(name "([^"]*)".*?\(number "([^"]*)"', re.S)

def use_lib(lib, name):
    key = f'{lib}:{name}'
    if key not in libdefs:
        b = lib_block(lib, name)
        pins = {num: (float(x), float(y)) for _, x, y, _, _, num in PINRE.findall(b)}
        libdefs[key] = (b.replace(f'(symbol "{name}"', f'(symbol "{key}"', 1), pins)
    return key

def custom(name, left, right, w):
    """left/right: list of (number, name, type) or None for a gap. Pins point inward."""
    n = max(len(left), len(right))
    h = max(20.32, math.ceil(((n - 1) * 2.54 + 7.62) / 2.54) * 2.54)
    s = f'(symbol {q("Arm:" + name)} (pin_names (offset 1.016)) (pin_numbers (hide yes)) (exclude_from_sim no) (in_bom yes) (on_board yes)\n'
    s += f'(property "Reference" "U" (at 0 {g(h/2+2.54)} 0) (effects (font (size 1.27 1.27))))\n'
    s += f'(property "Value" {q(name)} (at 0 {g(-h/2-2.54)} 0) (effects (font (size 1.27 1.27))))\n'
    s += f'(symbol {q(name + "_0_1")} (rectangle (start {-w/2} {h/2}) (end {w/2} {-h/2}) (stroke (width 0.254) (type default)) (fill (type background))))\n(symbol {q(name + "_1_1")}\n'
    pins = {}
    for side, ps in (('L', left), ('R', right)):
        top = (len(ps) - 1) * 2.54 / 2
        for i, p in enumerate(ps):
            if p is None:
                continue
            num, nm, typ = p
            y = g(top - i * 2.54)
            x = g((-1 if side == 'L' else 1) * (w / 2 + 5.08))
            pins[num] = (x, y)
            s += (f'(pin {typ} line (at {x} {y} {0 if side == "L" else 180}) (length 5.08) '
                  f'(name {q(nm)} (effects (font (size 1.016 1.016)))) (number {q(num)} (effects (font (size 1.016 1.016)))))\n')
    libdefs['Arm:' + name] = (s + '))', pins)
    BODY_H['Arm:' + name] = h
    return 'Arm:' + name

def rot(px, py, a):
    r = math.radians(a)
    return px * math.cos(r) - py * math.sin(r), px * math.sin(r) + py * math.cos(r)

class Part:
    def __init__(self, lib_id, ref, value, x, y, a=0, hide_ref=False, labels_right=False):
        self.lib_id, self.ref, self.x, self.y, self.a = lib_id, ref, g(x), g(y), a
        hid = ' (hide yes)' if hide_ref else ''
        X, Y = self.x, self.y
        if lib_id.startswith('Arm:'):
            hh = BODY_H[lib_id] / 2
            rp, vp, j = (X, g(Y - hh - 2.54)), (X, g(Y + hh + 2.54)), ''
        elif lib_id.startswith('power:'):
            up = -1 if value == 'GND' else 1            # graphic direction in library coords
            dx, dy = rot(0, up, a)
            dx, dy = round(dx), -round(dy)              # to schematic coords
            dist = 6.35
            rp = (X, Y)
            vp = (g(X + dx * dist), g(Y + dy * dist))
            j = ' (justify left)' if dx > 0 else (' (justify right)' if dx < 0 else '')
        elif labels_right:
            rp, vp, j = (g(X - 3.81), g(Y - 1.27)), (g(X - 3.81), g(Y + 1.27)), ' (justify left)'  # rotated text: left = visually right-aligned
        elif a in (90, 270):
            rp, vp, j = (X, g(Y - 3.81)), (X, g(Y + 3.81)), ''
        else:
            rp, vp, j = (g(X + 3.81), g(Y - 1.27)), (g(X + 3.81), g(Y + 1.27)), ' (justify left)'
        ang = a if a in (90, 270) else 0
        items.append(
            f'(symbol (lib_id {q(lib_id)}) (at {self.x} {self.y} {a}) (unit 1) (exclude_from_sim no) (in_bom yes) (on_board yes) (dnp no) (uuid {uid()})\n'
            f'(property "Reference" {q(ref)} (at {rp[0]} {rp[1]} {ang}) (effects (font (size 1.27 1.27)){j}{hid}))\n'
            f'(property "Value" {q(value)} (at {vp[0]} {vp[1]} {ang}) (effects (font (size 1.27 1.27)){j}{" (hide yes)" if lib_id.startswith("power:") and value == "PWR_FLAG" else ""}))\n'
            f'(instances (project "custom_arm" (path {q("/" + ROOT)} (reference {q(ref)}) (unit 1)))))')
        self.used = set()

    def pin(self, num):
        px, py = libdefs[self.lib_id][1][num]
        rx, ry = rot(px, py, self.a)
        self.used.add(num)
        return (g(self.x + rx), g(self.y - ry))

    def nc_rest(self):
        for num in libdefs[self.lib_id][1]:
            if num not in self.used:
                x, y = self.pin(num)
                items.append(f'(no_connect (at {x} {y}) (uuid {uid()}))')

# Fix the visible text placement for custom boxes (reference above, value below the body)
def label_part(part, h):
    pass

def wire(*pts, color=None):
    st = '(stroke (width 0) (type default))' if color is None else f'(stroke (width 0.5) (type default) (color {color[0]} {color[1]} {color[2]} 1))'
    for a, b in zip(pts, pts[1:]):
        if a != b:
            items.append(f'(wire (pts (xy {a[0]} {a[1]}) (xy {b[0]} {b[1]})) {st} (uuid {uid()}))')

RED, BLACK = (200, 0, 0), (0, 0, 0)

def junction(p):
    items.append(f'(junction (at {p[0]} {p[1]}) (diameter 0) (color 0 0 0 0) (uuid {uid()}))')

def text(x, y, t, size=1.27):
    items.append(f'(text {q(t)} (exclude_from_sim no) (at {g(x)} {g(y)} 0) (effects (font (size {size} {size})) (justify left top)) (uuid {uid()}))')

def power(kind, p, a):
    """kind: GND, +5V, +24V, +6V, PWR_FLAG. a: rotation so the symbol points away from the wire."""
    lid = use_lib('power', kind)
    counters['pwr'] = counters.get('pwr', 0) + 1
    ref = ('#FLG' if kind == 'PWR_FLAG' else '#PWR') + f'{counters["pwr"]:03d}'
    Part(lid, ref, kind, p[0], p[1], a, hide_ref=True)

PW_RIGHT = {'GND': 90, '+5V': 270, '+24V': 270, '+6V': 270}
PW_LEFT = {'GND': 270, '+5V': 90, '+24V': 90, '+6V': 90}

def stub_power(pt, kind, side, length=5.08):
    end = (g(pt[0] + (length if side == 'R' else -length)), pt[1])
    wire(pt, end)
    power(kind, end, PW_RIGHT[kind] if side == 'R' else PW_LEFT[kind])

def route(a, b, cx):
    """Orthogonal route a -> (cx, a.y) -> (cx, b.y) -> b."""
    cx = g(cx)
    wire(a, (cx, a[1]), (cx, b[1]), b)

# ---------------------------------------------------------------- symbol definitions
P_ = 'passive'
mega_left = [('USB_VBUS', 'USB VBUS', P_), ('USB_DP', 'USB D+', P_), ('USB_DM', 'USB D-', P_), ('USB_GND', 'USB GND', P_), None,
             ('IOREF', 'IOREF', P_), ('RESET', 'RESET', P_), ('3V3', '3.3V', P_), ('P5V', '5V', 'power_out'),
             ('PGND1', 'GND', P_), ('PGND2', 'GND', P_), ('VIN', 'VIN', P_), None,
             ('AREF', 'AREF', P_), ('AGND', 'GND', P_), None] + [(f'A{i}', f'A{i}', P_) for i in range(16)]
special = {0: 'D0/RX0', 1: 'D1/TX0', 14: 'D14/TX3', 15: 'D15/RX3', 16: 'D16/TX2', 17: 'D17/RX2', 18: 'D18/TX1',
           19: 'D19/RX1', 20: 'D20/SDA', 21: 'D21/SCL', 50: 'D50/MISO', 51: 'D51/MOSI', 52: 'D52/SCK', 53: 'D53/SS'}
for i in list(range(2, 14)) + [44, 45, 46]:
    special.setdefault(i, f'D{i}~')
mega_right = [(f'D{i}', special.get(i, f'D{i}'), P_) for i in range(22)] + [None] + \
             [(f'D{i}', special.get(i, f'D{i}'), P_) for i in range(22, 54)] + \
             [('D5V1', '5V', P_), ('D5V2', '5V', P_), ('DGND1', 'GND', P_), ('DGND2', 'GND', P_)]
MEGA = custom('Arduino_Mega_2560_R3', mega_left, mega_right, 45.72)

pi_names = {1: '3V3', 2: '5V', 3: 'GPIO2 SDA', 4: '5V', 5: 'GPIO3 SCL', 6: 'GND', 7: 'GPIO4', 8: 'GPIO14 TXD', 9: 'GND',
            10: 'GPIO15 RXD', 11: 'GPIO17', 12: 'GPIO18', 13: 'GPIO27', 14: 'GND', 15: 'GPIO22', 16: 'GPIO23', 17: '3V3',
            18: 'GPIO24', 19: 'GPIO10 MOSI', 20: 'GND', 21: 'GPIO9 MISO', 22: 'GPIO25', 23: 'GPIO11 SCLK', 24: 'GPIO8 CE0',
            25: 'GND', 26: 'GPIO7 CE1', 27: 'ID_SD', 28: 'ID_SC', 29: 'GPIO5', 30: 'GND', 31: 'GPIO6', 32: 'GPIO12',
            33: 'GPIO13', 34: 'GND', 35: 'GPIO19', 36: 'GPIO16', 37: 'GPIO26', 38: 'GPIO20', 39: 'GND', 40: 'GPIO21'}
pi_left = [('USBC_5V', 'USB-C 5V IN', P_), ('USBC_GND', 'USB-C GND', P_), None] + \
          [(f'H{i}', f'{i} {pi_names[i]}', P_) for i in range(1, 41, 2)]
pi_right = [('USBA_VBUS', 'USB-A VBUS', P_), ('USBA_DP', 'USB-A D+', P_), ('USBA_DM', 'USB-A D-', P_), ('USBA_GND', 'USB-A GND', P_), None] + \
           [(f'H{i}', f'{i} {pi_names[i]}', P_) for i in range(2, 41, 2)]
PI = custom('Raspberry_Pi_5', pi_left, pi_right, 50.8)

TMC = custom('TMC2209_StepStick',
             [('1', 'EN', P_), ('2', 'MS1', P_), ('3', 'MS2', P_), ('4', 'PDN/UART RX', P_), ('5', 'PDN/UART TX', P_),
              ('6', 'CLK', P_), ('7', 'STEP', P_), ('8', 'DIR', P_)],
             [('16', 'VM', P_), ('15', 'GND', P_), ('14', 'B2', P_), ('13', 'B1', P_), ('12', 'A1', P_), ('11', 'A2', P_),
              ('10', 'VDD/VIO', P_), ('9', 'GND', P_)], 48.26)
MOTOR = custom('Stepper_NEMA17', [('4', 'B- (coil B)', P_), ('3', 'B+ (coil B)', P_), ('1', 'A+ (coil A)', P_), ('2', 'A- (coil A)', P_)], [], 40.64)
PSU = custom('PSU_24V_Enclosed', [],
             [('VP', '+V', 'power_out'), ('VN', '-V', 'power_out')], 45.72)
PIPSU = custom('Pi_USB_C_PSU', [], [('V5', '5.1V', P_), ('VG', 'GND', P_)], 40.64)
BUCK = custom('Buck_Module', [('VI', 'IN+', P_), ('GI', 'IN-', P_)], [('VO', 'OUT+', 'power_out'), ('GO', 'OUT-', P_)], 35.56)
R = use_lib('Device', 'R'); C = use_lib('Device', 'C'); CP = use_lib('Device', 'C_Polarized')
FUSE = use_lib('Device', 'Fuse'); SERVO = use_lib('Motor', 'Motor_Servo')
RELAY = custom('Relay_24V_SPST_NO', [('30', '30 COM', P_), ('85', '85 coil+', P_)], [('87', '87 NO', P_), ('86', '86 coil-', P_)], 20.32)
ESTOP = use_lib('Switch', 'SW_Push_Open')
ENC = custom('AS5600_Encoder_Module', [('OUT', 'OUT', P_), ('SDA', 'SDA', P_), ('SCL', 'SCL', P_), ('GPO', 'GPO', P_), ('PGO', 'PGO', P_)],
             [('VCC', 'VCC', P_), ('GND', 'GND', P_), ('DIR', 'DIR', P_)], 30.48)

text(20, 15, 'ROBOARM - FULL WIRING (REV C)', 3.81)
text(20, 22, 'Every board pin shown. Wires drawn between parts. Power rails use KiCad power symbols (+24V, +5V, +6V, GND). Unused pins carry no-connect flags.', 1.524)

# ---------------------------------------------------------------- AC + 24 V supply (top left)
psu = Part(PSU, 'PS1', 'Lab bench supply: 24 V, 3 A limit (later: Mean Well LRS-200-24)', 254.0, 71.12)
f0 = Part(FUSE, 'F0', '10 A main', 309.88, psu.pin('VP')[1], 90)
wire(psu.pin('VP'), f0.pin('1'))
VPY = f0.pin('2')[1]
k1 = Part(RELAY, 'K1', '24 V 30 A relay', 340.36, g(VPY + 1.27))
jt = (320.04, VPY)
wire(f0.pin('2'), jt, color=RED); wire(jt, k1.pin('30'), color=RED); junction(jt)
estop = Part(ESTOP, 'SW1', 'E-STOP (NC, latching)', 320.04, g(VPY + 12.7), 90, labels_right=True)
wire(jt, estop.pin('2'))
eb = estop.pin('1')
wire(eb, (eb[0], g(eb[1] + 2.54)), (322.58, g(eb[1] + 2.54)), (322.58, k1.pin('85')[1]), k1.pin('85'))
g86 = (g(k1.pin('86')[0] + 2.54), k1.pin('86')[1]); wire(k1.pin('86'), g86); power('GND', g86, 0)
p24 = (g(k1.pin('87')[0] + 7.62), VPY)
wire(k1.pin('87'), p24, color=RED)
power('+24V', p24, 0)
flag24 = (g(p24[0] + 5.08), VPY); wire(p24, flag24); junction(p24); power('PWR_FLAG', flag24, 270)
text(299.72, 46.99, 'E-STOP: pressing SW1 opens the relay coil circuit, K1 drops out\nand the red 24 V bus goes dead. Pi and Mega stay on.\nA broken E-stop wire also stops the motors (fail-safe).', 1.27)
gnd_src = (g(psu.pin('VN')[0] + 7.62), psu.pin('VN')[1])
stub_power(psu.pin('VN'), 'GND', 'R', 7.62)
text(205.74, 88.9, 'PS1 for first tests: existing bench supply, 24 V, current limit 3 A.\nIts output on/off button cuts motor power only; Pi and Mega stay on.\nThe 24 V goes ONLY to the motor drivers and the servo buck. The Pi has its own USB-C supply (PS2).', 1.27)

# ---------------------------------------------------------------- Pi supply + Pi 5
pipsu = Part(PIPSU, 'PS2', 'Official Pi 27 W USB-C supply', 76.2, 152.4)
pi = Part(PI, 'U1', 'Raspberry Pi 5 8GB', 172.72, 299.72)
route(pipsu.pin('V5'), pi.pin('USBC_5V'), 116.84)
g1 = (g(pipsu.pin('VG')[0] + 5.08), pipsu.pin('VG')[1])
wire(pipsu.pin('VG'), g1); junction(g1); power('GND', g1, 0)
route(g1, pi.pin('USBC_GND'), 119.38)

# ---------------------------------------------------------------- Mega
mega = Part(MEGA, 'U2', 'Arduino Mega 2560 R3', 299.72, 299.72)
for k, (a, b) in enumerate([('USBA_VBUS', 'USB_VBUS'), ('USBA_DP', 'USB_DP'), ('USBA_DM', 'USB_DM')]):
    route(pi.pin(a), mega.pin(b), 236.22 + k * 2.54)
gg = (g(pi.pin('USBA_GND')[0] + 5.08), pi.pin('USBA_GND')[1])
wire(pi.pin('USBA_GND'), gg); junction(gg); power('GND', gg, 0)
route(gg, mega.pin('USB_GND'), 243.84)
text(120.65, 342.9, 'Pi USB-A to Mega USB-B cable:\npowers the Mega and carries commands.', 1.27)
stub_power(mega.pin('P5V'), '+5V', 'L')
for gp in ('PGND1', 'PGND2', 'AGND'):
    stub_power(mega.pin(gp), 'GND', 'L')
for gp in ('DGND1', 'DGND2'):
    stub_power(mega.pin(gp), 'GND', 'R')
for vp in ('D5V1', 'D5V2'):
    stub_power(mega.pin(vp), '+5V', 'R')

# ---------------------------------------------------------------- drivers + motors
DRV_X, MOT_X = 469.9, 571.5
joint = ['Base', 'Shoulder', 'Elbow', 'Wrist roll', 'Wrist pitch', 'Tool roll']
chan = iter([g(330.2 + k * 2.54) for k in range(40)])
drivers, motors = [], []
for i in range(6):
    yd = g(93.98 + i * 81.28)
    d = Part(TMC, f'DRV{i+1}', 'TMC2209 module (StepStick)', DRV_X, yd)
    m = Part(MOTOR, f'M{i+1}', '17HS19-2004S1' if i < 3 else '17HS08-1004S', MOT_X, yd)
    drivers.append(d); motors.append(m)
    for a, b in (('14', '4'), ('13', '3'), ('12', '1'), ('11', '2')):
        wire(d.pin(a), m.pin(b))
    stub_power(d.pin('10'), '+5V', 'R'); stub_power(d.pin('9'), 'GND', 'R')
    addr = i % 3                                  # bus A: DRV1-3, bus B: DRV4-6, addresses 0,1,2
    stub_power(d.pin('2'), '+5V' if addr == 1 else 'GND', 'L')   # MS1 = address bit 0
    stub_power(d.pin('3'), '+5V' if addr == 2 else 'GND', 'L')   # MS2 = address bit 1
    stub_power(d.pin('6'), 'GND', 'L')                           # CLK = internal clock
    text(MOT_X - 20.32, yd + 13.97, f'J{i+1} {joint[i]}: ' + ('0.59 Nm 2 A, set 1.4 A RMS' if i < 3 else '0.16 Nm 1 A, set 0.7 A RMS'), 1.27)

# ---------------------------------------------------------------- drawn 24 V bus (red) and motor ground return (black)
BUS24_X, BUSG_X = 515.62, 520.7
Y24, YG = 40.64, 43.18
taps24, tapsg = [Y24], [YG]
caps = []
for i, d in enumerate(drivers):
    vm, gp = d.pin('16'), d.pin('15')
    cy_ = g(vm[1] - 10.16)
    cp = Part(CP, f'C{20+i}', '100uF 35V', g(BUSG_X + 12.7), cy_)
    caps.append(cp)
    t1, b1 = cp.pin('1'), cp.pin('2')
    wire(vm, (BUS24_X, vm[1]), color=RED); taps24.append(vm[1])
    wire(gp, (BUSG_X, gp[1]), color=BLACK); tapsg.append(gp[1])
    wire((BUS24_X, t1[1]), t1, color=RED); taps24.append(t1[1])
    wire((BUSG_X, b1[1]), b1, color=BLACK); tapsg.append(b1[1])
# Mega -> STEP / DIR / EN, with EN pull-ups beside each module
for i, d in enumerate(drivers):
    for sig, mpin, dpin in (('STEP', f'D{22+i}', '7'), ('DIR', f'D{30+i}', '8')):
        route(mega.pin(mpin), d.pin(dpin), next(chan))
for i, d in enumerate(drivers):
    en = d.pin('1')
    xr = g(en[0] - 10.16)
    cxe = next(chan)
    a = mega.pin(f'D{36+i}')
    wire(a, (cxe, a[1]), (cxe, en[1]), (xr, en[1]), en)
    r = Part(R, f'R{21+i}', '10k', xr, g(en[1] - 10.16))
    wire(r.pin('2'), (xr, en[1])); junction((xr, en[1]))
    power('+5V', r.pin('1'), 0)
for d in drivers:
    d.used.add('4'); d.nc_rest()
for m in motors:
    m.nc_rest()

# ---------------------------------------------------------------- joint encoders (AS5600, absolute angle on each joint output)
NODE_X = 680.72
for i in range(6):
    a = mega.pin(f'A{i}')
    cxl = g(266.7 - i * 2.54)              # channel left of the Mega
    ycorr = g(448.94 + i * 2.54)            # corridor between DRV5 and DRV6
    xup = g(632.46 + i * 2.54)
    yn = g(drivers[i].y + 2.54)
    node = (NODE_X, yn)
    wire(a, (cxl, a[1]), (cxl, ycorr), (xup, ycorr), (xup, yn), node)
    cf = Part(C, f'C{1+i}', '100nF', NODE_X, g(yn + 10.16))
    wire(cf.pin('1'), node); power('GND', cf.pin('2'), 0)
    rs = Part(R, f'R{1+i}', '1k', g(NODE_X + 12.7), yn, 90)
    wire(node, rs.pin('1')); junction(node)
    enc = Part(ENC, f'ENC{1+i}', f'J{i+1} encoder, AS5600 module', 726.44, g(yn + 5.08))
    wire(rs.pin('2'), enc.pin('OUT'))
    stub_power(enc.pin('VCC'), '+5V', 'R'); stub_power(enc.pin('GND'), 'GND', 'R')
    stub_power(enc.pin('DIR'), 'GND', 'R', 10.16)
    enc.nc_rest()
text(660.4, 22.86, 'Joint encoders: AS5600 reads a magnet on each joint OUTPUT shaft (after the gearbox), so the angle is absolute at power-up.\nOUT = analog angle (0-5 V) to Mega A0-A5 through 1k + 100 nF at the Mega end. DIR tied to GND sets direction.\nCheck the module runs at 5 V (VCC) before buying; SDA/SCL left free for later I2C use.', 1.27)

# ---------------------------------------------------------------- gripper servo + 6 V supply (wired off the 24 V bus)
ORANGE = (200, 100, 0)
Y_R, Y_GR = 538.48, 571.5
taps24.append(Y_R); tapsg.append(Y_GR)
f1 = Part(FUSE, 'F1', '2 A', 530.86, Y_R, 90)
wire((BUS24_X, Y_R), f1.pin('1'), color=RED)
buck = Part(BUCK, 'U6', 'XL4015 buck, set 6.0 V', 558.8, g(Y_R + 1.27))
wire(f1.pin('2'), buck.pin('VI'), color=RED)
f2 = Part(FUSE, 'F2', '3 A', 591.82, Y_R, 90)
wire(buck.pin('VO'), f2.pin('1'), color=ORANGE)
p6 = (601.98, Y_R)
wire(f2.pin('2'), p6, color=ORANGE); power('+6V', p6, 0)
fl6 = (p6[0], g(p6[1] + 5.08)); wire(p6, fl6); junction(p6); power('PWR_FLAG', fl6, 180)
c7 = Part(CP, 'C7', '1000uF', 607.06, 548.64)
c8 = Part(C, 'C8', '100nF', 619.76, 548.64)
servo = Part(SERVO, 'M7', 'MG995 / MG996R gripper servo', 645.16, Y_R)
rail6 = [p6[0], 607.06, 619.76, servo.pin('2')[0]]
for a, b in zip(rail6, rail6[1:]):
    wire((a, Y_R), (b, Y_R), color=ORANGE)
for x in rail6[1:-1]:
    junction((x, Y_R))
wire((607.06, Y_R), c7.pin('1'), color=ORANGE)
wire((619.76, Y_R), c8.pin('1'), color=ORANGE)
# ground rail along the bottom, fed from the black return bus
gx_in = g(buck.pin('GI')[0] - 2.54)
gx_out = g(buck.pin('GO')[0] + 2.54)
gx_srv = g(servo.pin('3')[0] - 2.54)
wire(buck.pin('GI'), (gx_in, buck.pin('GI')[1]), (gx_in, Y_GR), color=BLACK)
wire(buck.pin('GO'), (gx_out, buck.pin('GO')[1]), (gx_out, Y_GR), color=BLACK)
wire(c7.pin('2'), (607.06, Y_GR), color=BLACK)
wire(c8.pin('2'), (619.76, Y_GR), color=BLACK)
wire(servo.pin('3'), (gx_srv, servo.pin('3')[1]), (gx_srv, Y_GR), color=BLACK)
railg = sorted({BUSG_X, gx_in, gx_out, 607.06, 619.76, gx_srv})
for a, b in zip(railg, railg[1:]):
    wire((a, Y_GR), (b, Y_GR), color=BLACK)
for x in railg[1:-1]:
    junction((x, Y_GR))
# gripper PWM from Mega D9 through R13
r13 = Part(R, 'R13', '1k', 629.92, 528.32)
wire(r13.pin('2'), (629.92, servo.pin('1')[1]), servo.pin('1'))
cxs = next(chan)
a9 = mega.pin('D9')
wire(a9, (cxs, a9[1]), (cxs, 520.7), (629.92, 520.7), r13.pin('1'))

# ---------------------------------------------------------------- TMC2209 UART load/diagnostic buses (StallGuard)
for grp, (txp, rxp, trunk_x, yrx, ytx, rref) in enumerate((('D16', 'D17', 420.37, 78.74, 81.28, 'R31'),
                                                           ('D14', 'D15', 422.91, 322.58, 325.12, 'R32'))):
    members = drivers[grp * 3:grp * 3 + 3]
    a_rx, a_tx = mega.pin(rxp), mega.pin(txp)
    c_rx, c_tx = next(chan), next(chan)
    wire(a_rx, (c_rx, a_rx[1]), (c_rx, yrx), (trunk_x, yrx))
    rt = Part(R, rref, '1k (UART TX)', g(trunk_x - 10.16), ytx, 90)
    wire(a_tx, (c_tx, a_tx[1]), (c_tx, ytx), rt.pin('1'))
    wire(rt.pin('2'), (trunk_x, ytx))
    taps = [yrx, ytx]
    for d in members:
        pin4 = d.pin('4')
        wire(pin4, (trunk_x, pin4[1])); taps.append(pin4[1])
    ys = sorted(taps)
    for a, b in zip(ys, ys[1:]):
        wire((trunk_x, a), (trunk_x, b))
    for y in ys[1:-1]:
        junction((trunk_x, y))
text(375.92, 29.21, 'UART bus A: Mega Serial2 (TX2 D16 via 1k, RX2 D17) -> PDN/UART of DRV1-3 (addr 0,1,2).\nUART bus B: Mega Serial3 (TX3 D14 via 1k, RX3 D15) -> DRV4-6. Gives per-joint load (StallGuard), temperature and open-wire flags.', 1.27)
text(527.05, 575.31, 'Gripper power: 24 V bus -> F1 -> U6 buck (set 6.0 V with a meter BEFORE connecting the servo) -> F2 -> 6 V (orange) -> C7, C8, servo.', 1.27)

wire(p24, (p24[0], Y24), (BUS24_X, Y24), color=RED)
wire(gnd_src, (gnd_src[0], YG), (BUSG_X, YG), color=BLACK)
junction(gnd_src)
for xb, taps, col in ((BUS24_X, taps24, RED), (BUSG_X, tapsg, BLACK)):
    ys = sorted(set(taps))
    for a, b in zip(ys, ys[1:]):
        wire((xb, a), (xb, b), color=col)
    for y in ys[1:-1]:
        junction((xb, y))
text(205.74, 106.68, '24 V BUS (red): bench supply + -> F0 -> VM on every driver. Ground return (black): every driver GND -> bench supply -', 1.27)


# ---------------------------------------------------------------- notes
text(40.64, 535.94,
     'NOTES\n'
     '1. Mega pins: STEP D22-27, DIR D30-35, EN D36-41 (LOW = driver on; 10k pull-ups keep drivers OFF while the Mega boots), encoders A0-A5, gripper PWM D9.\n'
     '2. TMC2209 standalone mode: UART mode: MS1/MS2 set each driver bus address (0-2), microstep is set over UART. CLK = GND selects the internal clock.\n'
     '3. Check pin names against the silkscreen of the TMC2209 modules you buy (vendors differ). Set phase current with the module trimmer before connecting the arm.\n'
     '4. TMC2209 VM max is about 29 V: 24 V only. Never plug or unplug a motor with 24 V present. Verify coil pairs with an ohmmeter.\n'
     '5. Modules sit in female headers on perfboard. Heatsink on every module, 40 mm fan over the row.\n'
     '6. All grounds common. Never connect 24 V or 6 V to the Mega 5 V pins.', 1.524)

# ---------------------------------------------------------------- bill of materials (all Amazon)
BOM_ROWS = [
    ('Ref', 'Qty', 'Part', 'Buy on Amazon (ASIN)', 'Est.'),
    ('U1', '1', 'Raspberry Pi 5 8GB', 'not included', '-'),
    ('PS2', '1', 'Official Raspberry Pi 27 W USB-C supply', 'not included', '-'),
    ('U2', '1', 'Arduino Mega 2560 R3', 'not included', '-'),
    ('PS1', '1', 'Lab bench supply, 24 V, 3 A limit', 'not included', '-'),
    ('DRV1-DRV6', '6', 'BIGTREETECH TMC2209 V1.3 + heatsink', '5-pack + 1 single (B07ZQ3C1XW)', '$40'),
    ('M1-M3', '3', 'STEPPERONLINE Nema 17 17HS19-2004S1, 59 Ncm 2 A', '3-pack (B00Y2HJE22)', '$30'),
    ('M4-M6', '3', 'STEPPERONLINE Nema 17 17HS08-1004S, 16 Ncm 1 A', '3 singles (B00PNEQ79Q)', '$33'),
    ('M7', '1', 'MG996R servo (gripper)', '4-pack (B0DK1V5ZSM)', '$17'),
    ('U6', '1', 'XL4015 5 A buck module, set 6.0 V', '3-pack (B00LOG4XC0)', '$10'),
    ('ENC1-ENC6', '6', 'AS5600 magnetic encoder module + diametric magnet', '10-pack (B0D3WMK5MT)', '$15'),
    ('F0-F2', '3', 'Inline ATO fuse holder + fuses', '5-pack kit (B0B4JTWJDT)', '$12'),
    ('SW1', '1', 'E-stop, 22 mm latching mushroom, 1 NC', 'COMOK (B07MJPRMRL)', '$9'),
    ('K1', '1', '24 V 30 A relay, normally open, with socket', 'ObabO-type 24 V with socket (B0CQFG7WZV)', '$8'),
    ('C7, C20-C25', '7', 'Electrolytic 1000 uF 16 V (x1), 100 uF 35 V (x6)', 'assortment (B0DDCB76H9)', '$12'),
    ('C1-C6, C8', '7', 'Ceramic 100 nF', 'assortment (B07P8N8BW9)', '$10'),
    ('R1-R6, R13, R21-R26, R31-R32', '15', '1k (x9), 10k (x6) metal film 1/4 W', 'ELEGOO kit (B072BL2VX1)', '$10'),
    ('-', '1', 'Driver carrier: prototype board', 'ElectroCookie 3-pack (B082KY5Y5Z)', '$12'),
    ('-', '1', '2.54 mm female headers (driver sockets)', 'Glarks kit (B076GZXW3Z)', '$8'),
    ('-', '1', '40 mm 5 V fan over driver row', 'WINSINN 2-pack (B08R9JJDYP)', '$9'),
    ('-', '1', 'USB-A to USB-B cable (Pi to Mega)', 'Amazon Basics (B00NH11KIK)', '$5'),
    ('-', '1', '18 AWG silicone wire (24 V, motors)', 'CBAZY kit (B073RDBW7L)', '$15'),
    ('-', '1', '22 AWG silicone wire (signals)', 'CBAZY kit (B073RF4YY4)', '$13'),
    ('TOTAL', '', 'New purchases, estimate before tax and shipping', '', '$268'),
]
BX, BY = 30.48, 363.22
text(BX, g(BY - 5.08), 'BILL OF MATERIALS (all Amazon; prices are estimates, check the cart; full links in bom.csv)', 1.524)
for col, x in zip(range(5), (0, 30.48, 40.64, 132.08, 200.66)):
    text(BX + x, BY, '\n'.join(r[col] for r in BOM_ROWS), 1.27)

# ---------------------------------------------------------------- unused pins on boards
for prt in (mega, pi, psu, pipsu, buck):
    prt.nc_rest()

# ---------------------------------------------------------------- write
lib = '\n'.join(v[0] for v in libdefs.values())
sch = (f'(kicad_sch (version 20250114) (generator "eeschema") (generator_version "9.0") (uuid {ROOT}) (paper "A1")\n'
       f'(title_block (title "RoboArm - full wiring") (date "2026-10-03") (rev "C") (company "RoboArm") (comment 1 "Module wiring - not a validated machine"))\n'
       f'(lib_symbols {lib})\n' + '\n'.join(items) +
       '\n(sheet_instances (path "/" (page "1")))\n(embedded_fonts no))\n')
for old in ('controller.kicad_sch', 'joints_1_3.kicad_sch', 'joints_4_6.kicad_sch', 'homing_gripper.kicad_sch'):
    (P / old).unlink(missing_ok=True)
(P / 'custom_arm.kicad_sch').write_text(sch, encoding='utf8')
arm_syms = [v[0] for k, v in libdefs.items() if k.startswith('Arm:')]
(P / 'ArmModules.kicad_sym').write_text('(kicad_symbol_lib (version 20241209) (generator "kicad_symbol_editor")\n' +
                                        '\n'.join(s.replace('"Arm:', '"', 1) for s in arm_syms) + '\n)', encoding='utf8')
(P / 'sym-lib-table').write_text('(sym_lib_table (version 7) (lib (name "Arm") (type "KiCad") (uri "${KIPRJMOD}/ArmModules.kicad_sym") (options "") (descr "Arm board symbols")))', encoding='utf8')
print('wrote', len(items), 'items')
