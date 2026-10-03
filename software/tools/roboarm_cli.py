#!/usr/bin/env python3
"""Tiny terminal for the RoboArm Mega (real board or mock_mega.py).

    python3 roboarm_cli.py /dev/ttyACM0         # interactive
    python3 roboarm_cli.py /dev/pts/3 --demo    # scripted smoke test

Sends a ping every 0.5 s in the background so the firmware's link watchdog
does not trip while you type.
"""
import argparse
import sys
import threading
import time

import serial


def reader(ser, stop):
    while not stop.is_set():
        line = ser.readline().decode(errors="ignore").strip()
        if line and line != "OK pong":
            print(f"< {line}", flush=True)


def keepalive(ser, stop, lock):
    while not stop.is_set():
        with lock:
            ser.write(b"P\n")
        time.sleep(0.5)


def demo(send):
    steps = [("H", 0.3), ("E 1", 0.3), ("V 60", 0.2), ("M 30 20 -10 0 15 0", 0.2),
             ("S", 1.5), ("S", 0.2), ("G C", 0.2), ("M 0 0 0 0 0 0", 1.5), ("S", 0.2), ("E 0", 0.2)]
    for cmd, wait in steps:
        send(cmd)
        time.sleep(wait)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("port")
    ap.add_argument("--baud", type=int, default=115200)
    ap.add_argument("--demo", action="store_true")
    a = ap.parse_args()
    ser = serial.Serial(a.port, a.baud, timeout=0.2)
    time.sleep(2.0 if "ACM" in a.port or "USB" in a.port else 0.1)  # real Mega resets on open
    stop, lock = threading.Event(), threading.Lock()
    threading.Thread(target=reader, args=(ser, stop), daemon=True).start()
    threading.Thread(target=keepalive, args=(ser, stop, lock), daemon=True).start()

    def send(cmd):
        print(f"> {cmd}", flush=True)
        with lock:
            ser.write((cmd + "\n").encode())

    try:
        if a.demo:
            demo(send)
        else:
            for line in sys.stdin:
                send(line.strip())
    finally:
        stop.set()
        time.sleep(0.3)


if __name__ == "__main__":
    main()
