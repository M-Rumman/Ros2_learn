import rclpy
from rclpy.node import Node
from std_msgs.msg import String

class talkerNode(Node):
    def __init__(self):
        super().__init__('talker_node')
        self.publisher = self.create_publisher(String, 'topic', 10)
        timer_period = 0.5
        self.timer = self.create_timer(timer_period, self.timer_callback)
        self.count = 0
        
    def timer_callback(self):
        msg = String()
        msg.data = f"Hello world {self.count}"
        self.count+=1
        self.get_logger().info(f"Publishing {msg.data}")
        
def main(args=None):
    rclpy.init(args=args)
    #instance
    talker_node = talkerNode()
    #use node
    rclpy.spin(talkerNode)
    #destroy node
    talkerNode.destroy_node()
    rclpy.shutdown()
    
if __name__ == "__main__":
    main()