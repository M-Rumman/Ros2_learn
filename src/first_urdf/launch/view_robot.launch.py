import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
import xacro


def generate_launch_description():
    pkg_share = get_package_share_directory('first_urdf')

    # Convert Xacro to URDF XML string
    xacro_file = os.path.join(pkg_share, 'urdf', 'robot.xacro')
    robot_description_raw = xacro.process_file(xacro_file).toxml()

    use_sim_time = LaunchConfiguration('use_sim_time', default='true')

    rviz_config_file = os.path.join(pkg_share, 'rviz', 'mecanum_view.rviz')

    node_robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        output='screen',
        parameters=[{
            'robot_description': robot_description_raw,
            'use_sim_time': use_sim_time
        }]
    )

    # GUI sliders to manually move each continuous joint (wheels + rollers)
    # so you can visually confirm joints and meshes are correctly wired up.
    node_joint_state_publisher = Node(
        package='joint_state_publisher',
        executable='joint_state_publisher',
        name='joint_state_publisher',
        output='screen',
        parameters=[{
            'use_sim_time': use_sim_time,
            'source_list': ['joint_states'],
            'publish_default_positions': True,
            'ignore_timestamp': False,
        }]
    )

    node_rviz = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        output='screen',
        parameters=[{'use_sim_time': use_sim_time}],
        arguments=['-d', rviz_config_file] if os.path.exists(rviz_config_file) else [],
    )

    return LaunchDescription([
        DeclareLaunchArgument(
            'use_sim_time',
            default_value='true',
            description='Use simulation (Gazebo) clock if true'
        ),
        node_robot_state_publisher,
        node_joint_state_publisher,
        node_rviz,
    ])