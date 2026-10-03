# RoboArm development image: ROS 2 Jazzy (Ubuntu 24.04) + firmware toolchain.
# Builds for amd64 (dev VM/container) and arm64 (Raspberry Pi 5) from the same file.
FROM ros:jazzy-ros-base

ARG DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
        python3-serial python3-pip python3-colcon-common-extensions \
        ros-jazzy-ros2-control ros-jazzy-ros2-controllers ros-jazzy-xacro \
        ros-jazzy-robot-state-publisher ros-jazzy-joint-state-publisher \
        socat curl git nano \
    && rm -rf /var/lib/apt/lists/*

# Arduino CLI + AVR core + libraries, so the Mega firmware builds inside the image
RUN curl -fsSL https://raw.githubusercontent.com/arduino/arduino-cli/master/install.sh | BINDIR=/usr/local/bin sh \
    && arduino-cli core update-index \
    && arduino-cli core install arduino:avr \
    && arduino-cli lib install TMCStepper Servo

WORKDIR /roboarm
RUN echo 'source /opt/ros/jazzy/setup.bash' >> /root/.bashrc
CMD ["bash"]
