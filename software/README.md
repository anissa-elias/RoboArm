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

## Planned packages

| Package | Purpose |
|---|---|
| `roboarm_description` | URDF model of the arm |
| `roboarm_hardware` | ros2_control hardware interface talking to the Mega over USB serial |
| `roboarm_moveit_config` | MoveIt 2 motion planning |
| `roboarm_bringup` | Launch files |
| `roboarm_sim` | Simulation (MuJoCo or Gazebo) |
