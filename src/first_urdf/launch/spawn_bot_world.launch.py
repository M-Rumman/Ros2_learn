import os
import re
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

    # Load and clean URDF/XACRO
    xacro_file = os.path.join(pkg_share, 'urdf', 'robot.xacro')
    robot_description_raw = xacro.process_file(xacro_file).toxml()
    robot_description_raw = re.sub(r'<!--.*?-->', '', robot_description_raw, flags=re.DOTALL)
    if robot_description_raw.startswith('<?xml'):
        robot_description_raw = robot_description_raw[robot_description_raw.index('?>') + 2:].strip()

    use_sim_time = LaunchConfiguration('use_sim_time', default='true')
    
    x_pose = LaunchConfiguration('x_pose', default='-7.0')
    y_pose = LaunchConfiguration('y_pose', default='5.0')
    z_pose = LaunchConfiguration('z_pose', default='0.06')
    yaw_pose = LaunchConfiguration('yaw', default='0.0')

    # Path to your new custom Gazebo world file (Change filename if different)
    world_path = os.path.join(pkg_share, 'worlds', 'hospital.world')

    # 1. Gazebo Server & Client
    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            os.path.join(get_package_share_directory('gazebo_ros'), 'launch', 'gazebo.launch.py')
        ]),
        launch_arguments={
            'world': world_path,
        }.items()
    )

    # 2. Robot State Publisher
    node_robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        output='screen',
        parameters=[{
            'robot_description': robot_description_raw,
            'use_sim_time': use_sim_time,
        }]
    )

    # 3. Spawn Robot in Gazebo
    spawn_entity = Node(
        package='gazebo_ros',
        executable='spawn_entity.py',
        arguments=[
            '-topic', 'robot_description',
            '-entity', 'mecanum_bot',
            '-x', x_pose,
            '-y', y_pose,
            '-z', z_pose,
            '-Y', yaw_pose
        ],
        output='screen'
    )

    # 4. Joint State Broadcaster Spawner
    joint_state_broadcaster_spawner = Node(
        package='controller_manager',
        executable='spawner',
        arguments=['joint_state_broadcaster', '--controller-manager', '/controller_manager'],
        parameters=[{'use_sim_time': use_sim_time}],
    )

    # 5. Mecanum Drive Controller Spawner
    mecanum_drive_controller_spawner = Node(
        package='controller_manager',
        executable='spawner',
        arguments=['mecanum_drive_controller'],
        parameters=[{'use_sim_time': use_sim_time}],
        output='screen'
    )

    # 6. Optional Relay for easy teleop via /cmd_vel
    cmd_vel_relay = Node(
        package='topic_tools',
        executable='relay',
        name='cmd_vel_relay',
        arguments=['/cmd_vel', '/mecanum_drive_controller/reference_unstamped'],
        parameters=[{'use_sim_time': use_sim_time}],
        output='screen',
    )

    return LaunchDescription([
        DeclareLaunchArgument(
            'use_sim_time',
            default_value='true',
            description='Use simulation (Gazebo) clock'
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
        ),
        cmd_vel_relay,
    ])