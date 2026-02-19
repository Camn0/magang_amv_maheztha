# Magang AMV: BlueBoat Autonomous Vision Navigation (Tugas 2)

This ROS 2 package upgrades the BlueBoat USV from manual teleoperation to an autonomous Vision Pilot. It uses a custom-trained YOLOv12 model to detect red and green buoys and automatically steers the differential thrusters to navigate the boat through the gap between them.

## Demo Visualization & Example Detection

**Autonomous Navigation Demo:**
[Screencast from 02-20-2026 03:05:12 AM.webm](https://github.com/user-attachments/assets/9e9f2b0e-ea09-4b90-90bc-93eb35040426)

> **Note:** Watch the demonstration of the boat automatically steering through the buoy gap in the Stonefish simulator.

**YOLOv12 "X-Ray" Debug View:**

> **Note:** The `/vision_debug/image` feed showing real-time bounding boxes, class labels, and confidence scores directly from the neural network.

## Model Training Process

The object detection model (`best.pt`) was custom-trained to recognize the specific buoys in the simulator environment.

1. **Dataset Collection:** Images of the red and green buoys were captured directly from the simulated camera feed to ensure accurate lighting and color representation.
2. **Jupyter Notebook (`Tugas2_Training.ipynb`):** The training pipeline is documented in the included Google Colab notebook.
3. **Training via YOLOv12:** The dataset was fed into the Ultralytics YOLOv12 architecture, leveraging Colab's cloud GPUs to train the model over multiple epochs until high confidence scores were consistently achieved.
4. **Deployment:** The resulting `best.pt` weights file was exported and integrated directly into the ROS 2 node.

## Key Features

* **Real-time Object Detection:** Uses YOLOv12 to actively scan the camera feed for `red_ball` and `green_ball` classes.
* **Smart Proximity Tracking:** Automatically calculates bounding box areas to lock onto the *closest* buoys, ignoring distant ones in the background.
* **Autonomous Steering Logic:** Calculates the horizontal midpoint between detected buoys and acts as a "bang-bang" controller to keep the boat perfectly aligned with the gap.
* **Failsafe & Obstacle Avoidance:** Automatically stops if no buoys are detected, and applies directional offsets if only one buoy is visible to prevent collisions.
* **Non-Blocking Debug Feed:** Publishes an annotated video stream (`/vision_debug/image`) for monitoring the AI's "brain" via `rqt_image_view` without slowing down the control loop.

## System Architecture

The data flow connects the simulated camera, the AI brain, and the motor outputs:

| Node | Topic | Message Type | Description |
| --- | --- | --- | --- |
| **`vision_controller`** | `/sonobot/camera/image_color` | `sensor_msgs/Image` | **Subscriber:** Receives the raw camera feed from the simulator. |
| **`vision_controller`** | `/vision_debug/image` | `sensor_msgs/Image` | **Publisher:** Outputs the annotated frame with YOLO bounding boxes. |
| **`vision_controller`** | `/blueboat/setpoint/pwm` | `std_msgs/Float64MultiArray` | **Publisher:** Sends `[-right, left]` thrust values. |

## Installation

### Prerequisites

* Ubuntu 22.04 / ROS 2 Humble
* Python 3
* **Ultralytics & OpenCV** (Required for the AI model and image processing)
* **ROS 2 CV Bridge** (Required to convert ROS image messages to OpenCV)

### Steps

1. **Install Python & ROS Dependencies:**

```bash
sudo apt install ros-humble-cv-bridge ros-humble-vision-opencv
pip3 install ultralytics opencv-python

```

2. **Clone & Build:**

```bash
cd ~/ros2_ws/src
# (Ensure your folder structure matches the tree and best.pt is included)
cd ~/ros2_ws
colcon build --packages-select magang_amv_maheztha

```

3. **Source the Workspace:**

```bash
source install/setup.bash

```

## How to Run

1. **Launch the Simulation:**
*(Ensure the Stonefish/Gazebo simulator and the boat's camera are running first)*
2. **Run the Vision Pilot Node:**

```bash
ros2 run magang_amv_maheztha vision_pilot

```

3. **View the Debug Camera Feed (Optional but Recommended):**
Open a new terminal window and run:

```bash
ros2 run rqt_image_view rqt_image_view

```

*Select `/vision_debug/image` from the dropdown menu to see exactly what the AI sees.*

## Configuration

To adjust the navigation behavior, edit the variables in `vision_node.py` under the `__init__` function:

```python
# src/magang_amv_maheztha/magang_amv_maheztha/vision_node.py
self.center_tolerance = 70  # Increase to reduce wobble; decrease for tighter gap alignment
self.forward_speed = 10.0   # Adjust the base cruising speed
self.turn_speed = 3.0       # Adjust how aggressively the boat steers left/right

```

---

Would you like me to walk you through generating the `.gif` or `.mp4` file of your simulation screen so you can insert it into the placeholder links?
