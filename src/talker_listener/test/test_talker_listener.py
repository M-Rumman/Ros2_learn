import os
import sys
import unittest
import uuid
import time

import launch
import launch_ros
import launch_ros.actions
import launch_testing.actions
import pytest

import rclpy

import std_msgs.msg

#launch feature node using launch description. This is used to launch the talker and listener nodes in test mode
@pytest.mark.launch_test
def generate_test_description(): #Tells ros2 which nodes need to be running for the test to happen
    file_path = os.path.dirname(__file__) #grabs the path of the directory where the test file lives
    talker_node = launch_ros.actions.Node(
        executable=sys.executable, #this tells ros to use the current python interpreter to run the script
        arguments=[os.path.join(
            file_path, "..", "talker_listener", 'talker_node.py')], #The path to the talker node
        additional_env={'PYTHONUNBUFFERED': '1'}, #this order python to print its output immediately instead of caching it to see the real time logs
        parameters=[{
            "topic": "talker_topic"
        }]
    )
    listener_node = launch_ros.actions.Node(
        executable=sys.executable,
        arguments=[os.path.join(
            file_path, "..", "talker_listener", 'listener_node.py')],
        additional_env={'PYTHONUNBUFFERED': '1'},
        parameters=[{
            "topic": "listener_topic"
        }]
    )
    
    return (
        launch.LaunchDescription([
            talker_node,
            listener_node,
            launch_testing.actions.ReadyToTest(), #This is a signal that tells the framework that the nodes are running now and are ready to start verification test
        ]),
        {
            'talker': talker_node,
            'listener': listener_node,
        }
    )

#test node
class TestTalkerListener(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls): #run once before and after starting the test suite
        #initialize ros context for the test node
        rclpy.init()
        
    @classmethod
    def tearDownClass(cls):
        rclpy.shutdown()
        
    def setUp(self): #run before and after every individual test function, so every time a test starts it initializes the test node
        #Create a ROS node for tests
        self.node = rclpy.create_node('test_talker_listener_link')
        
    def tearDown(self):
        self.node.destroy_node()
        
    def test_talker_transmits(self, talker, proc_output):
        msgs_rx = []
        
        sub = self.node.create_subscription(
            std_msgs.msg.String,
            'talker_topic',
            lambda msg: msgs_rx.append(msg),
            10
        )
        time.sleep(2)
        try:
            #wait until the talker transmits two messages over the ROS topic
            end_time = time.time() + 10
            while time.time() < end_time:
                rclpy.spin_once(self.node, timeout_sec=0.1)
                if len(msgs_rx) > 2:
                    break
            self.assertGreater(len(msgs_rx), 2)
            
            #Make sure the talker also output the same data via stdout
            for msg in msgs_rx:
                proc_output.assertWaitFor(
                    expected_output=msg.data, process=talker
                )
        finally:
            self.node.destroy_subscription(sub)
    
    def test_listener_receives(self, listener, proc_output):
        pub = self.node.create_publisher(
            std_msgs.msg.String,
            'listener_topic',
            10
        )
        time.sleep(2)   
        try:
            #publish a uniques message on chatter and verify that the listener gets it and prints it
            msg = std_msgs.msg.String()
            msg.data = str(uuid.uuid4())
            for _ in range(10):
                pub.publish(msg)
                success = proc_output.waitFor(
                    expected_output=msg.data,
                    process=listener,
                    timeout=1.0,
                )
                if success:
                    break
            assert success, 'Waiting for output timed out'
        finally:
            self.node.destroy_publisher(pub)
        