#!/usr/bin/env python3
"""Fake RoboArm Mega: speaks the firmware's serial protocol with nothing connected.

Creates a pseudo-terminal and prints its path; point any client (ROS 2 hardware
interface, roboarm_cli.py) at it as if it were /dev/ttyACM0.

    python3 mock_mega.py            # prints e.g. "mock Mega on /dev/pts/3"
    python3 roboarm_cli.py /dev/pts/3

Joints move toward their targets at the configured speed, like the real firmware
in RA_SIM mode. Protocol reference: firmware/roboarm_mega/roboarm_mega.ino.
"""
import os
import pty
import select
import time
import tty

N = 6
LIMIT_MIN = [-170, -90, -135, -170, -110, -180]
LIMIT_MAX = [170, 90, 135, 170, 110, 180]


class Arm:
    def __init__(self):
        self.pos = [0.0] * N
        self.target = [0.0] * N
        self.vmax = 30.0
        self.enabled = False
        self.faults = 0
        self.stream_dt = 0.0
        self.gripper = 20
        self.last_rx = time.monotonic()

    def step(self, dt):
        if not self.enabled:
            return
        dist = [abs(t - p) for t, p in zip(self.target, self.pos)]
        longest = max(dist) or 1.0
        for j in range(N):
            v = self.vmax * max(dist[j] / longest, 0.05)
            d = self.target[j] - self.pos[j]
            move = max(-v * dt, min(v * dt, d))
            self.pos[j] += move
        if time.monotonic() - self.last_rx > 1.0:   # link watchdog, like the firmware
            self.faults |= 1
            self.enabled = False
            return "FAULT 1"

    def moving(self):
        return any(abs(t - p) > 1e-3 for t, p in zip(self.target, self.pos))

    def status(self):
        cmd = " ".join(f"{p:.2f}" for p in self.pos)
        load = " ".join("200" for _ in range(N))
        drv = " ".join("1" for _ in range(N))
        return f"S {self.faults} {int(self.enabled)} {int(self.moving())} | {cmd} | {cmd} | {load} | {drv}"

    def handle(self, line):
        parts = line.split()
        if not parts:
            return None
        c, args = parts[0].upper(), parts[1:]
        clamp = lambda j, a: max(LIMIT_MIN[j], min(LIMIT_MAX[j], a))
        try:
            if c == "P":
                return "OK pong"
            if c == "E":
                on = args and args[0] != "0"
                if on and self.faults:
                    return "ERR faults active, send C to clear"
                self.enabled = bool(on)
                if not on:
                    self.target = list(self.pos)
                return "OK"
            if c == "M":
                a = [float(x) for x in args[:N]]
                if len(a) < N:
                    return "ERR need 6 angles"
                if not self.enabled:
                    return "ERR disabled, send E 1"
                self.target = [clamp(j, a[j]) for j in range(N)]
                return "OK"
            if c == "J":
                j = int(args[0]) - 1
                if not 0 <= j < N:
                    return "ERR joint 1-6"
                if not self.enabled:
                    return "ERR disabled, send E 1"
                self.target[j] = clamp(j, float(args[1]))
                return "OK"
            if c == "X":
                self.target = list(self.pos)
                return "OK"
            if c == "V":
                self.vmax = max(0.1, float(args[0]))
                return "OK"
            if c == "A":
                return "OK"
            if c == "G":
                self.gripper = {"O": 20, "C": 110}.get(args[0].upper(), None) or int(args[0])
                return "OK"
            if c == "S":
                return self.status()
            if c == "T":
                hz = max(0, min(50, int(args[0])))
                self.stream_dt = 1.0 / hz if hz else 0.0
                return "OK"
            if c == "Z":
                self.pos = [0.0] * N
                self.target = [0.0] * N
                return "OK zeroed"
            if c in ("R", "L"):
                return "OK"
            if c == "C":
                self.faults = 0
                return "OK cleared"
            if c == "H":
                return "RoboArm commands: P E M J X V A G S T Z R L C H (see roboarm_mega.ino header)"
        except (ValueError, IndexError):
            return "ERR bad arguments"
        return "ERR unknown, H for help"


def main():
    master, slave = pty.openpty()
    tty.setraw(slave)               # no echo: the mock must not read back its own output
    print(f"mock Mega on {os.ttyname(slave)}", flush=True)
    arm = Arm()
    buf = b""
    last = time.monotonic()
    last_stream = last
    os.write(master, b"RoboArm firmware ready (MOCK)\r\n")
    while True:
        r, _, _ = select.select([master], [], [], 0.01)
        now = time.monotonic()
        out = []
        if r:
            buf += os.read(master, 1024)
            arm.last_rx = now
            while b"\n" in buf:
                line, buf = buf.split(b"\n", 1)
                reply = arm.handle(line.decode(errors="ignore").strip())
                if reply:
                    out.append(reply)
        ev = arm.step(now - last)
        if ev:
            out.append(ev)
        last = now
        if arm.stream_dt and now - last_stream >= arm.stream_dt:
            last_stream = now
            out.append(arm.status())
        for o in out:
            os.write(master, (o + "\r\n").encode())


if __name__ == "__main__":
    main()
