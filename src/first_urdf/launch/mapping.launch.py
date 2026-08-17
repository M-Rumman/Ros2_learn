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
    slam_toolbox_dir = get_package_share_directory('slam_toolbox')

    # Load URDF/Xacro
    xacro_file = os.path.join(pkg_share, 'urdf', 'robot.xacro')
    robot_description_raw = xacro.process_file(xacro_file).toxml()
    robot_description_raw = re.sub(r'<!--.*?-->', '', robot_description_raw, flags=re.DOTALL)
    if robot_description_raw.startswith('<?xml'):
        robot_description_raw = robot_description_raw[robot_description_raw.index('?>') + 2:].strip()

    use_sim_time = LaunchConfiguration('use_sim_time', default='true')
    
    # Set to your new world filename
    world_path = os.path.join(pkg_share, 'worlds', 'hospital.world')
    ekf_config_path = os.path.join(pkg_share, 'config', 'ekf.yaml')

    # 1. Gazebo
    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            os.path.join(get_package_share_directory('gazebo_ros'), 'launch', 'gazebo.launch.py')
        ]),
        launch_arguments={'world': world_path}.items()
    )

    # 2. Robot State Publisher
    node_robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        output='screen',
        parameters=[{'robot_description': robot_description_raw, 'use_sim_time': use_sim_time}]
    )

    # 3. Spawn Robot
    spawn_entity = Node(
        package='gazebo_ros',
        executable='spawn_entity.py',
        arguments=['-topic', 'robot_description', '-entity', 'mecanum_bot', '-z', '0.06'],
        output='screen'
    )

    # 4. Controllers
    joint_state_broadcaster = Node(
        package='controller_manager',
        executable='spawner',
        arguments=['joint_state_broadcaster', '--controller-manager', '/controller_manager'],
        parameters=[{'use_sim_time': use_sim_time}],
    )

    mecanum_drive_controller = Node(
        package='controller_manager',
        executable='spawner',
        arguments=['mecanum_drive_controller'],
        parameters=[{'use_sim_time': use_sim_time}],
        output='screen'
    )

    # 5. EKF Node
    ekf_node = Node(
        package='robot_localization',
        executable='ekf_node',
        name='ekf_filter_node',
        output='screen',
        parameters=[ekf_config_path, {'use_sim_time': use_sim_time}]
    )

    # 6. SLAM Toolbox (Online Async Mapping)
    slam_toolbox = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(slam_toolbox_dir, 'launch', 'online_async_launch.py')
        ),
        launch_arguments={
            'use_sim_time': 'true',
            'base_frame': 'base_footprint',
            'odom_frame': 'odom',
            'map_frame': 'map',
            'scan_topic': '/scan'
        }.items()
    )

    # 7. RViz2
    node_rviz = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        output='screen',
        parameters=[{'use_sim_time': use_sim_time}]
    )

    # 8. Cmd Vel Relay
    cmd_vel_relay = Node(
        package='topic_tools',
        executable='relay',
        name='cmd_vel_relay',
        arguments=['/cmd_vel', '/mecanum_drive_controller/reference_unstamped'],
        parameters=[{'use_sim_time': use_sim_time}],
        output='screen',
    )

    return LaunchDescription([
        DeclareLaunchArgument('use_sim_time', default_value='true'),
        gazebo,
        node_robot_state_publisher,
        spawn_entity,
        RegisterEventHandler(
            event_handler=OnProcessExit(
                target_action=spawn_entity,
                on_exit=[joint_state_broadcaster],
            )
        ),
        RegisterEventHandler(
            event_handler=OnProcessExit(
                target_action=joint_state_broadcaster,
                on_exit=[mecanum_drive_controller, ekf_node, slam_toolbox, node_rviz],
            )
        ),
        cmd_vel_relay,
    ])