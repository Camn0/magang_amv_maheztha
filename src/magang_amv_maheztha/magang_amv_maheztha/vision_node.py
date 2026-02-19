import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from std_msgs.msg import Float64MultiArray
from cv_bridge import CvBridge
import cv2
from ultralytics import YOLO

class VisionController(Node):
    def __init__(self):
        super().__init__('vision_controller')

        # 1. AI MODEL SETUP
        # Load the custom-trained YOLOv12 model for buoy detection
        self.model = YOLO('/home/kinarast/magang_amv_maheztha/src/magang_amv_maheztha/best.pt') 

        # 2. ROS COMMUNICATION INTERFACES
        # Subscribe to the simulated camera feed
        self.subscription = self.create_subscription(Image, '/sonobot/camera/image_color', self.image_callback, 10)
        
        # Publish motor commands to the thrusters
        self.publisher_ = self.create_publisher(Float64MultiArray, '/blueboat/setpoint/pwm', 10)
        
        # Publish a debug video feed so we can see what the AI sees without lagging the system
        self.debug_pub = self.create_publisher(Image, '/vision_debug/image', 10)
        
        # Utility to convert ROS Image messages to OpenCV format
        self.bridge = CvBridge()
        
        # 3. NAVIGATION PARAMETERS
        # How many pixels off-center the target can be before the boat needs to turn
        self.center_tolerance = 70  
        self.forward_speed = 10.0   
        self.turn_speed = 3.0       

    def image_callback(self, msg):
        # STEP 1: READ THE IMAGE
        try:
            # Convert ROS message to OpenCV image in standard BGR color space
            cv_image = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
            # Find the exact horizontal center of the camera view (usually 320 for a 640px image)
            image_center_x = cv_image.shape[1] // 2
        except Exception as e:
            self.get_logger().error(f'CV Bridge Error: {e}')
            return

        # STEP 2: RUN AI INFERENCE
        results = self.model(cv_image, verbose=False)

        # STEP 3: PUBLISH DEBUG FEED (X-RAY VISION)
        # Tell YOLO to draw its bounding boxes and labels onto a copy of the frame
        annotated_frame = results[0].plot()
        # Convert it back to a ROS message and publish it to rqt_image_view
        debug_msg = self.bridge.cv2_to_imgmsg(annotated_frame, encoding='bgr8')
        self.debug_pub.publish(debug_msg)

        # STEP 4: PARSE DETECTIONS
        red_box = None
        green_box = None
        
        # Track the area of the boxes. We only want to navigate using the CLOSEST 
        # (largest) balls, ignoring any tiny ones far away in the background.
        max_red_area = 0
        max_green_area = 0

        for r in results:
            for box in r.boxes:
                # Extract the class ID and confidence score for this specific detection
                cls = int(box.cls[0])
                confidence = float(box.conf[0])
                
                # Ignore detections the AI is less than 10% sure about
                if confidence < 0.1: 
                    continue 

                # Extract the box boundaries to calculate its center and size
                x1, y1, x2, y2 = box.xyxy[0]
                center_x = int((x1 + x2) / 2)
                area = (x2 - x1) * (y2 - y1)

                # Get the actual text label from the model (e.g., "red_ball")
                class_name = self.model.names[cls].lower()

                # Robust String Matching: 
                # If the word 'red' is in the label AND this is the biggest red ball we've seen so far:
                if 'red' in class_name and area > max_red_area:
                    red_box = center_x     # Save its X coordinate
                    max_red_area = area    # Update the max area tracker
                    
                # If the word 'green' is in the label AND this is the biggest green ball we've seen:
                elif 'green' in class_name and area > max_green_area:
                    green_box = center_x
                    max_green_area = area

        # STEP 5: NAVIGATION LOGIC (WHERE DO WE GO?)
        left_thrust = 0.0
        right_thrust = 0.0
        target_x = None

        if red_box is not None and green_box is not None:
            # Ideal Scenario: See both balls. Calculate the exact midpoint to drive through.
            target_x = (red_box + green_box) // 2
            self.get_logger().info(f'Seeing BOTH. Aiming for midpoint: {target_x}')
            
        elif red_box is not None:
            # Danger: Only see Red. Shift the target 50 pixels to the RIGHT to avoid crashing into it.
            target_x = red_box + 50 
            self.get_logger().info('Seeing RED only. Steering Right.')
            
        elif green_box is not None:
            # Danger: Only see Green. Shift the target 50 pixels to the LEFT to avoid crashing into it.
            target_x = green_box - 50 
            self.get_logger().info('Seeing GREEN only. Steering Left.')
            
        else:
            # Failsafe: See nothing. Stop the motors to prevent running away.
            self.get_logger().info('No balls detected.')
            self.publish_motors(0.0, 0.0)
            return

        # STEP 6: STEERING CONTROL (BANG-BANG CONTROLLER)
        # Error = Where we want to look (target_x) minus where we are currently looking (image_center_x)
        error = target_x - image_center_x
        
        if abs(error) < self.center_tolerance:
            # Aligned: Target is roughly in the center of the camera. Push both motors forward.
            left_thrust = self.forward_speed
            right_thrust = self.forward_speed
        elif error > 0:
            # Target is to the Right: Push left motor forward, right motor backward to spin right.
            left_thrust = self.turn_speed
            right_thrust = -self.turn_speed
        else:
            # Target is to the Left: Push right motor forward, left motor backward to spin left.
            left_thrust = -self.turn_speed
            right_thrust = self.turn_speed

        # Send the final calculated thrusts to the hardware/simulator
        self.publish_motors(left_thrust, right_thrust)

    def publish_motors(self, left, right):
        # Package the thrust values into the array format expected by the simulator
        # The specific mapping for this boat is [-right, left]
        msg = Float64MultiArray()
        msg.data = [-right, left] 
        self.publisher_.publish(msg)

def main(args=None):
    # Standard ROS 2 node lifecycle
    rclpy.init(args=args)
    vision_controller = VisionController()
    rclpy.spin(vision_controller)  # Keep the node alive and listening to the camera
    vision_controller.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()