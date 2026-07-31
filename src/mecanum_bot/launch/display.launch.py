"""Quick RViz check: loads robot.xacro, publishes robot_state_publisher and
joint_state_publisher_gui (sliders for every continuous joint), and opens
RViz2. Use this FIRST, before Gazebo, to visually confirm:
  - the box base_link appears with four wheels at the four corners of a
    square (equal spacing),
  - each wheel's hub axis points sideways (Y), not up/down,
  - moving a roller slider spins that roller about the correct tilted axis.
"""
import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
import xacro


def generate_launch_description():
    pkg_share = get_package_share_directory('mecanum_bot')
    xacro_file = os.path.join(pkg_share, 'urdf', 'robot.xacro')
    robot_description_raw = xacro.process_file(xacro_file).toxml()

    use_sim_time = LaunchConfiguration('use_sim_time', default='false')

    return LaunchDescription([
        DeclareLaunchArgument('use_sim_time', default_value='false'),

        Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            output='screen',
            parameters=[{'robot_description': robot_description_raw,
                         'use_sim_time': use_sim_time}]
        ),
        Node(
            package='joint_state_publisher_gui',
            executable='joint_state_publisher_gui',
            output='screen',
        ),
        Node(
            package='rviz2',
            executable='rviz2',
            output='screen',
        ),
    ])
