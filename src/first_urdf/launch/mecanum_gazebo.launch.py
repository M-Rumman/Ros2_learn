import os
import re  # 
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, RegisterEventHandler
from launch.event_handlers import OnProcessExit
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
import xacro

def generate_launch_description():
    pkg_share = get_package_share_directory('first_urdf')

    # Convert Xacro parameters to explicit URDF structures
    xacro_file = os.path.join(pkg_share, 'urdf', 'robot.xacro')
    robot_description_raw = xacro.process_file(xacro_file).toxml()

    # REMOVE XML COMMENTS (Fixes gazebo_ros2_control parser error)
    robot_description_raw = re.sub(r'<!--.*?-->', '', robot_description_raw, flags=re.DOTALL)

    if robot_description_raw.startswith('<?xml'):
        robot_description_raw = robot_description_raw[
            robot_description_raw.index('?>') + 2:
        ].strip()

    use_sim_time = LaunchConfiguration('use_sim_time', default='true')

    node_robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        output='screen',
        parameters=[{
            'robot_description': robot_description_raw,
            'use_sim_time': use_sim_time
        }]
    )

    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            os.path.join(get_package_share_directory('gazebo_ros'), 'launch', 'gazebo.launch.py')
        ]),
    )

    # Spawn just above wheel-radius clearance so the robot settles onto
    # its wheels instead of free-falling from height and bouncing/tipping
    # (0.6 m was sized for a much larger robot).
    spawn_entity = Node(
        package='gazebo_ros',
        executable='spawn_entity.py',
        arguments=['-topic', 'robot_description', '-entity', 'mecanum_bot', '-z', '0.06'],
        output='screen'
    )

    joint_state_broadcaster_spawner = Node(
        package='controller_manager',
        executable='spawner',
        arguments=['joint_state_broadcaster', '--controller-manager', '/controller_manager'],
    )

    # The controller's own runtime topic (not the spawner CLI) is what
    # needs remapping: with use_stamped_vel:false it listens on
    # <ctrl_name>/reference_unstamped [geometry_msgs/Twist]. Remapping
    # '~/reference_unstamped' on the spawner node does not reach that
    # topic once the controller is loaded into controller_manager, so we
    # target the fully-qualified topic name instead.
    mecanum_drive_controller_spawner = Node(
        package='controller_manager',
        executable='spawner',
        arguments=['mecanum_drive_controller', '--controller-manager', '/controller_manager'],
        remappings=[
            ('/mecanum_drive_controller/reference_unstamped', '/cmd_vel'),
        ]
    )

    return LaunchDescription([
        DeclareLaunchArgument(
            'use_sim_time',
            default_value='true',
            description='Use simulation (Gazebo) clock if true'
        ),
        gazebo,
        node_robot_state_publisher,
        spawn_entity,
        RegisterEventHandler(
            event_handler=OnProcessExit(
                target_action=spawn_entity,
                on_exit=[joint_state_broadcaster_spawner],
            )
        ),
        RegisterEventHandler(
            event_handler=OnProcessExit(
                target_action=joint_state_broadcaster_spawner,
                on_exit=[mecanum_drive_controller_spawner],
            )
        )
    ])