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

        # 1. LOAD YOUR TRAINED MODEL
        # REPLACE THIS PATH with the actual path to your .pt file!
        self.model = YOLO('/home/kinarast/magang_amv_maheztha/src/magang_amv_maheztha/best.pt') 

        # 2. SUBSCRIBER (Camera Input)
        self.subscription = self.create_subscription(
            Image,
            '/sonobot/camera/image_color',
            self.image_callback,
            10)
        
        # 3. PUBLISHER (Motor Output)
        self.publisher_ = self.create_publisher(Float64MultiArray, '/blueboat/setpoint/pwm', 10)
        
        self.bridge = CvBridge()

        # CONFIGURATION
        self.center_tolerance = 50  # Pixels. If target is within this range, drive forward.
        self.forward_speed = 100.0   # Speed when driving straight
        self.turn_speed = 10.0       # Speed when rotating to align
        
        # IMAGE DATA
        self.image_width = 640  # Default, will update automatically

    def image_callback(self, msg):
        # A. CONVERT ROS IMAGE TO OPENCV
        try:
            cv_image = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
            self.image_width = cv_image.shape[1]
            image_center_x = self.image_width // 2
        except Exception as e:
            self.get_logger().error(f'CV Bridge Error: {e}')
            return

        # B. RUN YOLO INFERENCE
        results = self.model(cv_image, verbose=False)
        
        red_box = None
        green_box = None

        # C. PARSE DETECTIONS
        # Assuming class 0 = Red Ball, class 1 = Green Ball (CHECK YOUR MODEL'S CLASSES!)
        for r in results:
            boxes = r.boxes
            for box in boxes:
                cls = int(box.cls[0])
                confidence = float(box.conf[0])
                
                if confidence < 0.5: continue # Skip low confidence

                # Get center X of the box
                x1, y1, x2, y2 = box.xyxy[0]
                center_x = int((x1 + x2) / 2)

                # Logic to pick the "best" ball (e.g., the largest/closest one)
                # Here we just take the first valid one we see for simplicity
                if cls == 0: # Red Ball
                    red_box = center_x
                elif cls == 1: # Green Ball
                    green_box = center_x

        # D. CONTROL LOGIC
        left_thrust = 0.0
        right_thrust = 0.0
        
        target_x = None

        # CASE 1: See BOTH balls -> Aim for the MIDDLE
        if red_box is not None and green_box is not None:
            target_x = (red_box + green_box) // 2
            self.get_logger().info(f'Seeing BOTH. Aiming for midpoint: {target_x}')

        # CASE 2: See only RED -> Aim to the RIGHT of it
        elif red_box is not None:
            target_x = red_box + 100 # Offset to keep red on the left
            self.get_logger().info('Seeing RED only. Steering Right.')

        # CASE 3: See only GREEN -> Aim to the LEFT of it
        elif green_box is not None:
            target_x = green_box - 100 # Offset to keep green on the right
            self.get_logger().info('Seeing GREEN only. Steering Left.')

        # CASE 4: See NOTHING -> Stop or Rotate to search
        else:
            self.get_logger().info('No balls detected. Rotating.')
            self.publish_motors(-5.0, 5.0)
            return

        # E. CALCULATE ERROR & STEER
        error = target_x - image_center_x
        
        # Check alignment
        if abs(error) < self.center_tolerance:
            # ALIGNED: GO FORWARD
            left_thrust = self.forward_speed
            right_thrust = self.forward_speed
            action = "FORWARD"
        elif error > 0:
            # TARGET IS TO THE RIGHT: TURN RIGHT
            # (Left motor pushes, Right motor reverses/stops)
            left_thrust = self.turn_speed
            right_thrust = -self.turn_speed
            action = "TURN RIGHT"
        else:
            # TARGET IS TO THE LEFT: TURN LEFT
            left_thrust = -self.turn_speed
            right_thrust = self.turn_speed
            action = "TURN LEFT"

        # F. PUBLISH COMMANDS
        self.publish_motors(left_thrust, right_thrust)
        
        # Optional: Draw on image for debugging (show via cv2.imshow if running locally)
        cv2.circle(cv_image, (int(target_x), 100), 10, (255, 0, 0), -1)
        cv2.imshow("Vision Pilot", cv_image)
        cv2.waitKey(1)

    def publish_motors(self, left, right):
        msg = Float64MultiArray()
        # YOUR MAPPING: [-right, left]
        msg.data = [-right, left] 
        self.publisher_.publish(msg)

def main(args=None):
    rclpy.init(args=args)
    vision_controller = VisionController()
    rclpy.spin(vision_controller)
    vision_controller.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
