# Roadmap

## Done

- [x] Electronics architecture (Pi 5, Mega, TMC2209, AS5600, E-stop)
- [x] Full-pin KiCad schematic with automated connection check
- [x] Amazon bill of materials

## Next

### Mechanical
- [x] Choose the body: RoboArm body at Ned2 size (see mechanical-design.md)
- [x] Joint layout, gear ratios and motor sizes per joint (proposed, not yet tested)
- [ ] Encoder magnet mounts on each joint output
- [ ] Printed parts list, materials and print settings
- [ ] Assembly guide

### Electronics
- [ ] Order parts and bench-test one joint (driver, motor, encoder)
- [ ] Driver carrier perfboard layout
- [ ] Wiring harness and connectors per joint
- [ ] Optional: custom PCB replacing the perfboard

### Firmware (Arduino Mega)
- [ ] Six-axis step generation with acceleration
- [ ] Encoder reading and joint-angle calibration
- [ ] TMC2209 UART setup (current, microstepping, StallGuard)
- [ ] Collision detection and fault handling
- [ ] Serial protocol to the Pi

### Software (Raspberry Pi 5)
- [ ] URDF robot model
- [ ] ros2_control hardware interface
- [ ] MoveIt 2 configuration
- [ ] Simulation (MuJoCo or Gazebo)
- [ ] Simple operator UI

### Docs
- [ ] Build guide for students
- [ ] Safety checklist
