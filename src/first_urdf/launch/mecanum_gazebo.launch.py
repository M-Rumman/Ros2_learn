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
    nav2_bringup_dir = get_package_share_directory('nav2_bringup')

    xacro_file = os.path.join(pkg_share, 'urdf', 'robot.xacro')
    robot_description_raw = xacro.process_file(xacro_file).toxml()
    
    map_file = os.path.join(pkg_share, 'maps', 'mecanum_world_map.yaml')
    params_file = os.path.join(pkg_share, 'config', 'nav2_params.yaml')
    
    nav2_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(nav2_bringup_dir, 'launch', 'bringup_launch.py')
        ),
        launch_arguments={
            'map': map_file,
            'use_sim_time': 'true',
            'params_file': params_file,
            'autostart': 'true'
        }.items()
    )                              

    robot_description_raw = re.sub(r'<!--.*?-->', '', robot_description_raw, flags=re.DOTALL)

    if robot_description_raw.startswith('<?xml'):
        robot_description_raw = robot_description_raw[
            robot_description_raw.index('?>') + 2:
        ].strip()

    use_sim_time = LaunchConfiguration('use_sim_time', default='true')
    
    mecanum_controllers_yaml = os.path.join(pkg_share, 'config', 'mecanum_controllers.yaml')
    
    world_path = os.path.join(pkg_share, 'worlds', 'mecanumWorld.world')

    node_robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        output='screen',
        parameters=[{
            'robot_description': robot_description_raw,
            'use_sim_time': use_sim_time
        }]
    )
    
    node_joint_state_publisher = Node(
        package='joint_state_publisher',
        executable='joint_state_publisher',
        name='joint_state_publisher',
        output='screen',
        parameters=[{
            'use_sim_time': use_sim_time,
            'publish_default_positions': True,
            'ignore_timestamp': False,
        }]
    )

    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            os.path.join(get_package_share_directory('gazebo_ros'), 'launch', 'gazebo.launch.py')
        ]),
        launch_arguments={
            'world': world_path,
        }.items()
    )

    spawn_entity = Node(
        package='gazebo_ros',
        executable='spawn_entity.py',
        arguments=['-topic', 'robot_description', '-entity', 'mecanum_bot', '-z', '0.06'],
        output='screen'
    )
    
    node_rviz = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        output='screen',
        parameters=[{'use_sim_time': use_sim_time}],
        arguments=['-d', os.path.join(pkg_share, 'rviz', 'mecanum_view.rviz')] if os.path.exists(os.path.join(pkg_share, 'rviz', 'mecanum_view.rviz')) else [],
    )

    joint_state_broadcaster_spawner = Node(
        package='controller_manager',
        executable='spawner',
        arguments=['joint_state_broadcaster', '--controller-manager', '/controller_manager'],
        parameters=[{'use_sim_time': use_sim_time}],
    )

    mecanum_drive_controller_spawner = Node(
        package='controller_manager',
        executable='spawner',
        arguments=["mecanum_drive_controller"],
        parameters=[{'use_sim_time': use_sim_time}],
        output='screen'
    )    

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
                on_exit=[mecanum_drive_controller_spawner, node_rviz, node_joint_state_publisher, nav2_launch],
            )
        ),
        cmd_vel_relay,
    ])