"""Worst-case joint sizing for the Ned2-sized RoboArm. Run: python joint_sizing.py

Layout: J1 base (Z), J2 shoulder (Y), J3 elbow (Y), J4 wrist (Y), J5 wrist twist, J6 gripper.
Worst pose: arm stretched out horizontally.
Masses are ESTIMATES until parts are weighed; edit them here and re-run.
"""
import math

G = 9.81
SERVICE_FACTOR = 1.5   # acceleration and friction on top of static load
DRIVE_EFF = 0.85       # gearbox + belt efficiency
USABLE = 0.6           # usable fraction of holding torque at 24 V, moving, microstepped
SPRING_BALANCE = 0.6   # fraction of the arm's own J2 gravity load carried by the spring

# Lengths (m): upper arm, forearm, wrist to flange.
L2, L3, WRIST = 0.221, 0.215, 0.0685
GRIP_CG, TCP = 0.050, 0.110  # past the flange: gripper centre of mass, payload point (cad/gripper.py)

PAYLOAD = 0.300
M = dict(gripper=0.20, j5_motor=0.13, wrist=0.10, forearm=0.30, j4_motor=0.15,
         elbow=0.30, upper=0.45, j3_motor=0.60)

# motor: (holding N·m, rated A, run A)
MOTORS = {
    '17HS19-1684S': (0.52, 1.68, 1.4),
    '17HS08-1004S': (0.16, 1.00, 1.0),
    '11HS12-0674S': (0.06, 0.67, 0.67),
}
# joint: (motor, gearbox ratio, belt stage ratios, belt driven teeth, target deg/s)
DRIVES = {
    'J1': ('17HS19-1684S', 5.18, [8.0], 160, 45),
    'J2': ('17HS19-1684S', 13.73, [5.0], 100, 30),
    'J3': ('17HS19-1684S', 5.18, [5.0], 80, 45),
    'J4': ('17HS08-1004S', 1.0, [3.75, 5.0], 80, 90),
    'J5': ('11HS12-0674S', 1.0, [4.0], 64, 90),
}


def loads():
    pay = PAYLOAD
    wrist_mass = M['j5_motor'] + M['wrist']
    t4 = G * (pay * (WRIST + TCP) + M['gripper'] * (WRIST + GRIP_CG) + wrist_mass * 0.03)
    t5 = G * pay * 0.02                  # Ned2 rates payload at 20 mm offset
    t3 = G * (pay * (L3 + WRIST + TCP) + M['gripper'] * (L3 + WRIST + GRIP_CG)
              + wrist_mass * (L3 + 0.01) + M['forearm'] * L3 * 0.55
              + M['j4_motor'] * 0.09 + M['elbow'] * 0.01)
    past_elbow = (pay + M['gripper'] + wrist_mass + M['forearm'] + M['j4_motor'] + M['elbow'])
    # J3 motor sits on the upper arm 85 mm from the shoulder.
    t2_total = t3 + G * (past_elbow * L2 + M['upper'] * L2 * 0.5 + M['j3_motor'] * 0.085)
    t2_self = t2_total - G * pay * (L2 + L3 + WRIST + TCP)
    t2 = t2_total - SPRING_BALANCE * t2_self
    points = [(pay, L2 + L3 + WRIST + TCP), (M['gripper'], L2 + L3 + WRIST + GRIP_CG),
              (wrist_mass, L2 + L3), (M['forearm'], L2 + L3 * 0.55),
              (M['j4_motor'] + M['elbow'], L2), (M['upper'], L2 * 0.5)]
    inertia = sum(m * r * r for m, r in points)
    t1 = inertia * math.radians(60) + 0.33   # 60 deg/s^2 plus bearing friction
    return dict(J1=t1, J2=t2, J3=t3, J4=t4, J5=t5), t2_total


def report():
    t, t2_no_spring = loads()
    print(f'Reach from J2 to flange {1000 * (L2 + L3 + WRIST):.0f} mm, '
          f'estimated moving mass {sum(M.values()) + PAYLOAD:.2f} kg with payload\n')
    print('Joint  static  design  ratio  avail  margin  max deg/s  gbox out  belt N')
    for j, (motor, gbox, belts, teeth, target) in DRIVES.items():
        hold, rated, run = MOTORS[motor]
        usable = hold * min(run / rated, 1) * USABLE
        ratio = gbox * math.prod(belts)
        design = t[j] * SERVICE_FACTOR
        avail = usable * ratio * DRIVE_EFF
        speed = 10000 / (200 * 8 * ratio) * 360
        gbox_out = design / math.prod(belts) if gbox > 1 else 0
        radius = teeth * 2 / (2 * math.pi) / 1000
        print(f'{j:5} {t[j]:6.2f}  {design:6.2f}  {ratio:5.1f}  {avail:5.2f}  '
              f'{avail / design:6.2f}  {speed:6.0f}/{target:<3} {gbox_out:7.2f}  {design / radius:6.0f}')
    design = t2_no_spring * SERVICE_FACTOR
    print(f'\nJ2 with no spring: {t2_no_spring:.2f} static, {design:.2f} design, '
          f'{design / 5:.2f} at the gearbox, {design / 0.0318:.0f} N on the belt')


def extras():
    t, t2_no_spring = loads()
    print('\nDegrees of freedom (Grubler, spatial): M = 6(n - 1) - 5 x revolute joints')
    links, revolute = 6, 5
    print(f'  links {links}, revolute joints {revolute}: M = {6 * (links - 1) - 5 * revolute}')

    print('\nMoving mass by stage (kg):')
    wrist = M['j5_motor'] + M['wrist']
    stages = [('Payload', PAYLOAD), ('Gripper', M['gripper']), ('J5 motor and wrist', wrist),
              ('Forearm with J4 motor', M['forearm'] + M['j4_motor']), ('Elbow', M['elbow']),
              ('Upper arm', M['upper']), ('J3 motor and gearbox', M['j3_motor'])]
    for name, mass in stages:
        print(f'  {name:24} {mass:.2f}')
    total = sum(m for _, m in stages)
    print(f'  {"Total above J2":24} {total:.2f}')

    print('\nReach (mm):')
    print(f'  J2 to flange {1000 * (L2 + L3 + WRIST):.0f}, to payload point {1000 * (L2 + L3 + WRIST + TCP):.0f}')

    print('\nResolution:')
    for j, (motor, gbox, belts, _, _) in DRIVES.items():
        ratio = gbox * math.prod(belts)
        step = 360 / (200 * 8 * ratio)
        arm = {'J1': L2 + L3 + WRIST, 'J2': L2 + L3 + WRIST, 'J3': L3 + WRIST, 'J4': WRIST, 'J5': 0.03}[j]
        print(f'  {j}: {step:.4f} deg per microstep, {1000 * arm * math.radians(step):.3f} mm at the tip')

    print('\nBase tipping, arm fully out, about the base front edge:')
    base_mass = 1.9
    arm_cg = sum(m * r for m, r in [(PAYLOAD, L2 + L3 + WRIST + TCP), (M['gripper'], L2 + L3 + WRIST + GRIP_CG),
                                    (wrist, L2 + L3), (M['forearm'] + M['j4_motor'], L2 + L3 * 0.55),
                                    (M['elbow'], L2), (M['upper'], L2 / 2), (M['j3_motor'], 0.085)]) / total
    tip = total * (arm_cg - 0.1)
    keep = (base_mass) * 0.1
    print(f'  arm mass {total:.2f} kg at {1000 * arm_cg:.0f} mm from the axis: {G * tip:.2f} N·m tipping')
    print(f'  base {base_mass:.1f} kg at 100 mm: {G * keep:.2f} N·m resisting, ratio {keep / tip:.2f}')

    print('\nPower, estimates at 24 V:')
    runs = [('J1-J3', 3, 1.4, 1.65), ('J4', 1, 1.0, 2.1), ('J5', 1, 0.67, 4.5)]
    heat = sum(n * 2 * i * i * r for _, n, i, r in runs)
    print(f'  coil heat, all motors holding: {heat:.0f} W, about {heat / 24:.1f} A from the supply')
    print('  mechanical power, 5 N·m at J2 and 3 N·m at J3 at 30 deg/s: '
          f'{(5 + 3) * math.radians(30):.1f} W')
    print('  servo stall on 6 V: 2.5 A x 6 V = 15 W, about 0.7 A at 24 V')
    print(f'  design peak about {(heat + 15 + 10) / 0.85 / 24:.1f} A at 24 V')


if __name__ == '__main__':
    report()
    extras()
