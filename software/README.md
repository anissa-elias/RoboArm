# Software (Raspberry Pi 5)

Target: Ubuntu 24.04 with ROS 2 Jazzy on the Raspberry Pi 5, run in Docker so the same environment works on a dev machine and on the Pi.

## Dev environment (Docker)

`docker/Dockerfile` builds `roboarm-dev:jazzy`: ROS 2 Jazzy, ros2_control, Arduino CLI with the AVR core and firmware libraries, and Python serial tools. The same Dockerfile builds for amd64 (dev machine or VM) and arm64 (Raspberry Pi 5).

```bash
docker compose -f software/docker/compose.yaml build
docker compose -f software/docker/compose.yaml run --rm dev        # shell with the repo at /roboarm
```

On the Pi with the Mega plugged in, uncomment the `devices:` block in `compose.yaml` to pass `/dev/ttyACM0` into the container.

## Working with nothing connected

| Tool | Purpose |
|---|---|
| `tools/mock_mega.py` | Fake Mega on a virtual serial port; speaks the firmware protocol and moves joints at the set speed |
| `tools/roboarm_cli.py` | Terminal for the Mega (real or mock); `--demo` runs a scripted test |
| `tools/smoke_test.sh` | Builds the firmware and runs the CLI demo against the mock |

```bash
docker compose -f software/docker/compose.yaml run --rm dev bash software/tools/smoke_test.sh
```

## Simulator

`sim/roboarm.xml` is a MuJoCo model of the whole arm. The base and J1 use the real printable meshes; the arm above J1 uses simple shapes for now. Motor torques are limited to the values in `hardware/mechanical/joint_sizing.py`, and the J2 spring is not modeled.

```bash
cd software/sim
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python test_model.py     # checks holding and picking up a cube
.venv/bin/python play_web.py       # open http://localhost:8765
```

Over SSH, forward the port from your own computer with `ssh -L 8765:localhost:8765 <user>@<machine>`. To host it on a VPN address instead, start it with `ROBOARM_HOST=<address> .venv/bin/python play_web.py`. There is no login, so anyone who can reach that address can control it. With a local display you can also run `python -m mujoco.viewer --mjcf=roboarm.xml`.

## Planned packages

| Package | Purpose |
|---|---|
| `roboarm_description` | URDF model of the arm |
| `roboarm_hardware` | ros2_control hardware interface talking to the Mega over USB serial |
| `roboarm_moveit_config` | MoveIt 2 motion planning |
| `roboarm_bringup` | Launch files |
