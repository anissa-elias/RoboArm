"""Check the exported KiCad netlist against the intended connections."""
import re
import sys
from pathlib import Path

net = Path(sys.argv[1]).read_text(encoding='utf8')
nets = {}
for m in re.finditer(r'\(net \(code "?\d+"?\) \(name "([^"]*)"\)(.*?)\)\s*(?=\(net |\)\s*\)\s*$)', net, re.S):
    nodes = set(re.findall(r'\(node \(ref "([^"]+)"\) \(pin "([^"]+)"\)', m.group(2)))
    nets[m.group(1)] = nodes

def find(ref, pin):
    for name, nodes in nets.items():
        if (ref, pin) in nodes:
            return name, nodes
    return None, set()

fails = []
def same(*rp):
    n0, nodes = find(*rp[0])
    for r in rp[1:]:
        if r not in nodes:
            fails.append(f'{rp[0]} not connected to {r} (net {n0})')

def on(rp, netname):
    n, _ = find(*rp)
    if n != netname:
        fails.append(f'{rp} on net {n}, expected {netname}')

for i in range(6):
    d = f'DRV{i+1}'
    same(('U2', f'D{22+i}'), (d, '7'))
    same(('U2', f'D{30+i}'), (d, '8'))
    same(('U2', f'D{36+i}'), (d, '1'), (f'R{21+i}', '2'))
    on((f'R{21+i}', '1'), '+5V')
    for a, b in (('14', '4'), ('13', '3'), ('12', '1'), ('11', '2')):
        same((d, a), (f'M{i+1}', b))
    on((d, '16'), '+24V'); on((d, '15'), 'GND'); on((d, '9'), 'GND'); on((d, '10'), '+5V')
    addr = i % 3
    on((d, '2'), '+5V' if addr == 1 else 'GND'); on((d, '3'), '+5V' if addr == 2 else 'GND'); on((d, '6'), 'GND')
    same(('U2', f'A{i}'), (f'C{1+i}', '1'), (f'R{1+i}', '1'))
    same((f'R{1+i}', '2'), (f'ENC{1+i}', 'OUT'))
    on((f'ENC{1+i}', 'VCC'), '+5V'); on((f'ENC{1+i}', 'GND'), 'GND'); on((f'ENC{1+i}', 'DIR'), 'GND'); on((f'C{1+i}', '2'), 'GND')
    on((f'C{20+i}', '1'), '+24V'); on((f'C{20+i}', '2'), 'GND')
same(('U1', 'USBA_VBUS'), ('U2', 'USB_VBUS'))
same(('U1', 'USBA_DP'), ('U2', 'USB_DP'))
same(('U1', 'USBA_DM'), ('U2', 'USB_DM'))
on(('U1', 'USBA_GND'), 'GND'); on(('U2', 'USB_GND'), 'GND'); on(('U1', 'USBC_GND'), 'GND')
same(('PS2', 'V5'), ('U1', 'USBC_5V'))
on(('U2', 'P5V'), '+5V')
same(('PS1', 'VP'), ('F0', '1')); on(('PS1', 'VN'), 'GND')
same(('F0', '2'), ('K1', '30'), ('SW1', '2')); same(('SW1', '1'), ('K1', '85')); on(('K1', '86'), 'GND'); on(('K1', '87'), '+24V')
same(('U2', 'D17'), ('DRV1', '4'), ('DRV2', '4'), ('DRV3', '4'), ('R31', '2')); same(('U2', 'D16'), ('R31', '1'))
same(('U2', 'D15'), ('DRV4', '4'), ('DRV5', '4'), ('DRV6', '4'), ('R32', '2')); same(('U2', 'D14'), ('R32', '1'))
on(('F1', '1'), '+24V'); same(('F1', '2'), ('U6', 'VI')); same(('U6', 'VO'), ('F2', '1')); on(('F2', '2'), '+6V')
same(('U2', 'D9'), ('R13', '1')); same(('R13', '2'), ('M7', '1'))
on(('M7', '2'), '+6V'); on(('M7', '3'), 'GND')

print(f'{len(nets)} nets checked')
print('\n'.join(fails) if fails else 'ALL EXPECTED CONNECTIONS PRESENT')
sys.exit(1 if fails else 0)
