import sys
import rclpy
from rclpy.node import Node
from custom_interfaces.srv import AddTwoInts

class AdditionClientAsync(Node):
    def __init__(self):
        super().__init__("addition_client_async")
        self.client = self.create_client(AddTwoInts, "add_two_ints"
            )
        while not self.client.wait_for_service(timeout_sec = 1.0):
            self.get_logger().info("service not available, waiting...")
    def send_request(self):
        request = AddTwoInts.Request()
        request.a = int(sys.argv[1])
        request.b = int(sys.argv[2])
        self.future = self.client.call_async(request)

def main(args=None):
    rclpy.init(args=args)
    
    # Create node
    addition_client = AdditionClientAsync()
    addition_client.send_request()  
    
    # Spin node
    while rclpy.ok():
        rclpy.spin_once(addition_client)
        
        # Check if the future is done INSIDE the loop
        if addition_client.future.done():
            try:
                # Assign the result to 'response' so you can use it below
                response = addition_client.future.result()
            except Exception as e:
                addition_client.get_logger().info(f"Service call failed {e}")
            else:
                addition_client.get_logger().info(f"Received the sum: {response.sum}")
            
            # Break out of the while loop now that we have the result
            break
            
    #destroy and shutdown
    addition_client.destroy_node()
    rclpy.shutdown()
    
if __name__ == "__main__":
    main()
