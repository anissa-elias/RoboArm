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
L2, L3, WRIST = 0.221, 0.215, 0.055
GRIP_CG, TCP = 0.045, 0.090  # past the flange: gripper centre of mass, payload point

PAYLOAD = 0.300
M = dict(gripper=0.20, j5_motor=0.20, wrist=0.10, forearm=0.30, j4_motor=0.15,
         elbow=0.30, upper=0.45, j3_motor=0.60)

# motor: (holding N·m, rated A, run A)
MOTORS = {
    '17HS19-1684S': (0.52, 1.68, 1.4),
    '17HS08-1004S': (0.16, 1.00, 0.9),
    '11HS20-0674S': (0.12, 0.67, 0.67),
}
# joint: (motor, gearbox ratio, belt stage ratios, belt driven teeth, target deg/s)
DRIVES = {
    'J1': ('17HS19-1684S', 5.18, [8.0], 160, 45),
    'J2': ('17HS19-1684S', 13.73, [5.0], 100, 30),
    'J3': ('17HS19-1684S', 5.18, [5.0], 100, 45),
    'J4': ('17HS08-1004S', 1.0, [3.0, 5.0], 80, 90),
    'J5': ('11HS20-0674S', 1.0, [3.0], 48, 90),
}


def loads():
    pay = PAYLOAD
    wrist_mass = M['j5_motor'] + M['wrist']
    t4 = G * (pay * (WRIST + TCP) + M['gripper'] * (WRIST + GRIP_CG) + wrist_mass * 0.03)
    t5 = G * pay * 0.02                  # Ned2 rates payload at 20 mm offset
    t3 = G * (pay * (L3 + WRIST + TCP) + M['gripper'] * (L3 + WRIST + GRIP_CG)
              + wrist_mass * (L3 + 0.01) + M['forearm'] * L3 * 0.55
              + M['j4_motor'] * 0.04 + M['elbow'] * 0.01)
    past_elbow = (pay + M['gripper'] + wrist_mass + M['forearm'] + M['j4_motor'] + M['elbow'])
    # J3 motor sits on the upper arm 40 mm from the shoulder.
    t2_total = t3 + G * (past_elbow * L2 + M['upper'] * L2 * 0.5 + M['j3_motor'] * 0.04)
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


if __name__ == '__main__':
    report()
