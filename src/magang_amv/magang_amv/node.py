import rclpy
from rclpy.node import Node

# Import the specific message type
from std_msgs.msg import Float64MultiArray

# IMPORT KEYBOARD LISTENER
from pynput import keyboard

class MultiArrayPublisher(Node):

    def __init__(self):
        # 1. Initialize the node with a name
        super().__init__('multiarray_publisher')
        
        # 2. Create the publisher
        # Arguments: (Message Type, Topic Name, Queue Size)
        # TOPIC: /blueboat/setpoint/pwm
        self.publisher_ = self.create_publisher(Float64MultiArray, '/blueboat/setpoint/pwm', 10)
        
        # 3. Set a timer period (e.g., 0.1 seconds)
        timer_period = 0.1 
        self.timer = self.create_timer(timer_period, self.timer_callback)
        
        # INTERNAL VARIABLES FOR SPEED
        self.left_val = 0.0
        self.right_val = 0.0
        self.speed = 10.0  # The value you found works (10)

        # START KEYBOARD LISTENER (Non-blocking)
        self.listener = keyboard.Listener(on_press=self.on_press, on_release=self.on_release)
        self.listener.start()

    def on_press(self, key):
        try:
            # W = Forward (Both 10) -> Output [-10, 10]
            if key.char == 'w':
                self.left_val = self.speed
                self.right_val = self.speed
            # S = Backward (Both -10) -> Output [10, -10]
            elif key.char == 's':
                self.left_val = -self.speed
                self.right_val = -self.speed
            # A = Rotate Left (Left -10, Right 10) -> Output [-10, -10]
            elif key.char == 'a':
                self.left_val = -self.speed
                self.right_val = self.speed
            # D = Rotate Right (Left 10, Right -10) -> Output [10, 10]
            elif key.char == 'd':
                self.left_val = self.speed
                self.right_val = -self.speed
        except AttributeError:
            pass

    def on_release(self, key):
        # Stop when key is released
        self.left_val = 0.0
        self.right_val = 0.0

    def timer_callback(self):
        # This function runs every 'timer_period' seconds
        
        # A. Create the message object
        msg = Float64MultiArray()
        
        # B. LOGIC GOES HERE
        left_thruster = self.left_val
        right_thruster = self.right_val
        
        # Your specific mapping: [-right, left]
        # Forward (W): [-10, 10]  <-- Works if Right=10, Left=10
        # Spin CW (D): [10, 10]   <-- Works if Right=-10, Left=10
        msg.data = [-right_thruster, left_thruster]
        
        # C. Publish the message
        self.publisher_.publish(msg)
        
        # D. Log to console
        self.get_logger().info(f'Publishing: {msg.data}')

def main(args=None):
    # Initialize the ROS communication
    rclpy.init(args=args)
    
    # Create the node
    multi_array_publisher = MultiArrayPublisher()
    
    # Spin the node so the callbacks can execute
    rclpy.spin(multi_array_publisher)
    
    # Destroy the node explicitly (optional)
    multi_array_publisher.destroy_node()
    
    # Shutdown the ROS communication
    rclpy.shutdown()

if __name__ == '__main__':
    main()