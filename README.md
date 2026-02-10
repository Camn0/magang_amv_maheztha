# Magang AMV: BlueBoat Teleoperation

This ROS 2 package provides a lightweight teleoperation node for the BlueBoat USV (Unmanned Surface Vehicle). It captures keyboard inputs to control differential thrusters via PWM signals.

## Demo Visualization

[Screencast+from+02-10-2026+10_19_32+PM.webm](https://github.com/user-attachments/assets/cb4970c0-b2a7-48c2-b541-6cdefde75083)

> **Note:** Click the image above to watch the demonstration of the boat moving in the simulator.

## Key Features

* **Keyboard Control:** Uses `pynput` for non-blocking, real-time WASD control.
* **Differential Drive Logic:** Automatically mixes steering and throttle commands for tank-style turning.
* **Direct PWM Output:** Publishes `Float64MultiArray` directly to the `/blueboat/setpoint/pwm` topic.
* **Safety Default:** Automatically resets thrusters to neutral (0.0) when keys are released.

## System Architecture

The data flow is simple and direct:

| Node | Topic | Message Type | Description |
| --- | --- | --- | --- |
| **`multiarray_publisher`** | `/blueboat/setpoint/pwm` | `std_msgs/Float64MultiArray` | Sends `[-right, left]` thrust values. |

## Installation

### Prerequisites

* Ubuntu 22.04 / ROS 2 Humble
* Python 3
* **Pynput Library** (Required for keyboard listener)

### Steps

1. **Install Python Dependency:**
```bash
pip3 install pynput

```


2. **Clone & Build:**
```bash
cd ~/ros2_ws/src
# (Ensure your folder structure matches the tree below)
cd ~/ros2_ws
colcon build --packages-select magang_amv

```


3. **Source the Workspace:**
```bash
source install/setup.bash

```



## How to Run

1. **Launch the Simulation (Stonefish/Gazebo):**
*(Run your simulator launch command here first)*
2. **Run the Teleop Node:**
```bash
ros2 run magang_amv publisher

```


3. **Control the Boat:**
**Important:** You must keep the terminal window active (clicked) for keys to register.
| Key | Action | Motor Logic |
| --- | --- | --- |
| **W** | Move Forward | Left (+), Right (+) |
| **S** | Move Backward | Left (-), Right (-) |
| **A** | Spin Left | Left (-), Right (+) |
| **D** | Spin Right | Left (+), Right (-) |
| *(Release)* | Stop | Neutral (0, 0) |



## Configuration

To adjust the speed of the boat, edit the `speed` variable in `node.py`:

```python
# src/magang_amv/magang_amv/node.py
self.speed = 10.0  # Increase this value to make the boat faster

```
