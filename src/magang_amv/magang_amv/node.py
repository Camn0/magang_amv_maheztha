import rclpy
from rclpy.node import Node

# Import the specific message type
from std_msgs.msg import Float64MultiArray

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
        
        # Optional: Counter or internal state variables
        self.i = 0

    def timer_callback(self):
        # This function runs every 'timer_period' seconds
        
        # A. Create the message object
        msg = Float64MultiArray()
        
        # B. LOGIC GOES HERE
        # DATA: Two thrusters, (1500 is stopped)
        # Change these values to move: e.g., [1600.0, 1600.0] for forward
        msg.data = [1800.0, 1800.0]
        
        # C. Publish the message
        self.publisher_.publish(msg)
        
        # D. Log to console
        self.get_logger().info('Publishing array data...')

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