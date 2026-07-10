import os
from launch import LaunchDescription
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
    pkg_share = get_package_share_directory('first_urdf')
    urdf_path = os.path.join(pkg_share, 'urdf', 'block.urdf')

    with open(urdf_path, 'r') as infp:
        robot_description_content = infp.read()

    # Optional: Point to a saved rviz config if you create one later
    rviz_config_path = os.path.join(pkg_share, 'rviz', 'block_display.rviz')

    robot_state_publisher_node = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        output='screen',
        parameters=[{
            'robot_description': robot_description_content,
            'use_sim_time': False  # Explicitly set time source
        }]
    )

    # Added to handle joint states, though your joint is fixed, it keeps TF tree healthy
    joint_state_publisher_node = Node(
        package='joint_state_publisher',
        executable='joint_state_publisher',
        name='joint_state_publisher',
    )

    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        output='screen',
        arguments=['-d', rviz_config_path] #the -d flag tells rviz to load the saved display config when rviz2 is launched instead of a blank window
    )

    return LaunchDescription([
        robot_state_publisher_node,
        joint_state_publisher_node,
        rviz_node
    ])
