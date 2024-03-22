import launch
from launch.substitutions import Command, LaunchConfiguration
import launch_ros
from launch_ros.substitutions import FindPackageShare
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition
from launch import LaunchDescription
import os
from launch_ros.descriptions import ParameterValue

def generate_launch_description():
    # Constants for paths to different files and folders
    package_name = 'fusion2urdf_description'
    robot_name_in_model = 'fusion2urdf'
    robot_model_path = 'urdf/fusion2urdf.xacro'
    rviz_config_path = 'config/rviz_default.rviz'

    # Set path to files and directories
    pkg_share = FindPackageShare(package=package_name).find(package_name)
    default_robot_model_path = os.path.join(pkg_share, robot_model_path)
    default_rviz_config_path = os.path.join(pkg_share, rviz_config_path)

    # Launch configuration variables specific to simulation
    use_sim_time = LaunchConfiguration('use_sim_time')
    urdf_model = LaunchConfiguration('urdf_model')
    rviz_config_file = LaunchConfiguration('rviz_config_file')

    # Declare the launch arguments
    declare_use_sim_time = DeclareLaunchArgument(
        name='use_sim_time',
        default_value='false',
        description='Use simulation (Gazebo) clock if true')

    declare_robot_model_path = DeclareLaunchArgument(
        name='urdf_model', 
        default_value=default_robot_model_path, 
        description='Absolute path to robot urdf file')

    declare_rviz_config_path = DeclareLaunchArgument(
        name='rviz_config_file',
        default_value=default_rviz_config_path,
        description='Absolute path to rviz config file')

    # Publish the 3D pose of each link of robot  
    start_robot_state_publisher_node = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        parameters=[{'use_sim_time': use_sim_time},{'robot_description': ParameterValue(Command(['xacro ', default_robot_model_path]),value_type=str)}]
        )

    # Publish the joint states of the robot
    start_joint_state_publisher_node = Node(
        package='joint_state_publisher',
        executable='joint_state_publisher',
        name='joint_state_publisher',
        parameters= [{'use_sim_time': use_sim_time}])

    # Launch RViz
    start_rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        output='screen',
        arguments=['-d', rviz_config_file],
        parameters= [{'use_sim_time': use_sim_time}])

    # Create the launch description and populate
    ld = LaunchDescription()
 
    # Declare the launch options
    ld.add_action(declare_use_sim_time)
    ld.add_action(declare_robot_model_path)
    ld.add_action(declare_rviz_config_path)
    
    # Add any actions
    ld.add_action(start_joint_state_publisher_node)
    ld.add_action(start_robot_state_publisher_node)
    ld.add_action(start_rviz_node)
    
    return ld