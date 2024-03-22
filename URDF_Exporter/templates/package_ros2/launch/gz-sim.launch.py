import launch
from launch.substitutions import Command, LaunchConfiguration, PathJoinSubstitution
import launch_ros
from launch_ros.substitutions import FindPackageShare
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.conditions import IfCondition
from launch import LaunchDescription
import os
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
    # Constants for paths to different files and folders
    package_name = 'fusion2urdf_description'
    robot_name_in_model = 'fusion2urdf'
    robot_model_path = 'urdf/fusion2urdf.xacro'
    rviz_config_path = 'config/rviz_default.rviz'
    world_file_path = 'worlds/empty_world.sdf'

    # Pose where to spawn the robot
    spawn_x_val = '0.0'
    spawn_y_val = '0.0'
    spawn_z_val = '0.0'
    spawn_roll_val = '0.00'
    spawn_pitch_val = '0.00'
    spawn_yaw_val = '0.00'

    # Set path to files and directories
    pkg_gz_sim_ros = FindPackageShare(package='ros_gz_sim').find('ros_gz_sim')  
    pkg_share = FindPackageShare(package=package_name).find(package_name)
    default_robot_model_path = os.path.join(pkg_share, robot_model_path)
    default_rviz_config_path = os.path.join(pkg_share, rviz_config_path)
    default_world_path = os.path.join(pkg_share, world_file_path)

    # Launch configuration variables specific to simulation
    use_sim_time = LaunchConfiguration('use_sim_time')
    urdf_model = LaunchConfiguration('urdf_model')
    rviz_config_file = LaunchConfiguration('rviz_config_file')
    use_rviz = LaunchConfiguration('use_rviz')
    world = LaunchConfiguration('world')

    # Declare the launch arguments
    declare_use_sim_time = DeclareLaunchArgument(
        name='use_sim_time',
        default_value='False',
        description='Use simulation (Gazebo) clock if true')

    declare_robot_model_path = DeclareLaunchArgument(
        name='urdf_model', 
        default_value=default_robot_model_path, 
        description='Absolute path to robot urdf file')

    declare_rviz_config_path = DeclareLaunchArgument(
        name='rviz_config_file',
        default_value=default_rviz_config_path,
        description='Absolute path to rviz config file')

    declare_use_rviz = DeclareLaunchArgument(
        name='use_rviz',
        default_value='False',
        description='Whether to start RVIZ')

    declare_world = DeclareLaunchArgument(
        name='world',
        default_value=default_world_path,
        description='Full path to the world model file to load')

    # Subscribe to the joint states of the robot, and publish the 3D pose of each link.  
    start_robot_state_publisher_node = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        parameters=[
            {'use_sim_time': use_sim_time},
            {'robot_description': Command(['xacro ', urdf_model])}])

    # Publish the joint states of the robot
    start_joint_state_publisher_node = Node(
        package='joint_state_publisher',
        executable='joint_state_publisher',
        name='joint_state_publisher',
        parameters= [{'use_sim_time': use_sim_time}],)

    # Launch RViz
    start_rviz_node = Node(
        condition=IfCondition(use_rviz),
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        output='screen',
        arguments=['-d', rviz_config_file],
        parameters= [{'use_sim_time': use_sim_time}],)

    # Start Ignition Gazebo
    start_gz_sim = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(pkg_gz_sim_ros, 'launch', 'gz_sim.launch.py')),
        launch_arguments={"gz_args": world}.items(),
        )

    # Spawn robot
    spawn_entity = Node(
        package='ros_gz_sim', 
        executable='create',
        arguments=[
            '-name', robot_name_in_model,
            '-topic', 'robot_description',
            '-x', spawn_x_val,
            '-y', spawn_y_val,
            '-z', spawn_z_val,
            '-R', spawn_roll_val,
            '-P', spawn_pitch_val,
            '-Y', spawn_yaw_val],
        output='screen')

    # Create the launch description and populate
    ld = LaunchDescription()
 
    # Declare the launch options
    ld.add_action(declare_use_sim_time)
    ld.add_action(declare_robot_model_path)
    ld.add_action(declare_rviz_config_path)
    ld.add_action(declare_use_rviz)
    ld.add_action(declare_world)
    
    # Add any actions
    ld.add_action(start_gz_sim)
    ld.add_action(start_robot_state_publisher_node)
    ld.add_action(start_joint_state_publisher_node)
    ld.add_action(start_rviz_node)
    ld.add_action(spawn_entity)
    
    return ld