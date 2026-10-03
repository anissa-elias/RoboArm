#!/usr/bin/env bash
# Smoke test with nothing connected: builds the firmware and drives the mock Mega.
# Run inside the dev image:  docker compose -f software/docker/compose.yaml run --rm dev bash software/tools/smoke_test.sh
set -euo pipefail
cd "$(dirname "$0")/../.."
set +u; source /opt/ros/jazzy/setup.bash; set -u

echo "== ROS 2: $ROS_DISTRO"

echo "== firmware build (normal and SIM)"
arduino-cli compile -b arduino:avr:mega firmware/roboarm_mega | grep -E "Sketch uses"
arduino-cli compile -b arduino:avr:mega --build-property build.extra_flags=-DRA_SIM=1 firmware/roboarm_mega | grep -E "Sketch uses"

echo "== mock Mega + CLI demo"
python3 -u software/tools/mock_mega.py > /tmp/mock.log 2>&1 &
MOCK=$!
trap 'kill $MOCK 2>/dev/null || true' EXIT
sleep 1
PORT=$(head -1 /tmp/mock.log | awk '{print $NF}')
python3 software/tools/roboarm_cli.py "$PORT" --demo
