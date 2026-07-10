import rclpy
from rclpy.node import Node

from std_msgs.msg import String

class ListenerNode(Node):
    def __init__(self):
        super().__init__('listener_node')
        self.declare_parameter("topic", value="listener_topic")
        topic_name = self.get_parameter("topic").get_parameter_value().string_value
        # Correctly creates the subscription
        self.subscription = self.create_subscription(String, topic_name, self.listener_callback, 10)
        
    def listener_callback(self, msg):
        self.get_logger().info(f"Received {msg.data}")
        
def main(args=None):
    rclpy.init(args=args)
    
    # Create the node
    listener_node = ListenerNode()

    try:
        # Run/Spin the node so it can receive messages
        rclpy.spin(listener_node)
    except KeyboardInterrupt:
        # Handle Ctrl+C cleanly
        pass
    finally:
        # Destroy the node explicitly and shutdown
        listener_node.destroy_node()
        rclpy.shutdown()

if __name__ == "__main__":
    main()