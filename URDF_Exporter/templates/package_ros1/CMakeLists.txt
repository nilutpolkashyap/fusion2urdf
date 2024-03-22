cmake_minimum_required(VERSION 2.8.3)
project(fusion2urdf_description)

find_package(catkin REQUIRED COMPONENTS
  rospy roscpp
)

catkin_package(
#  INCLUDE_DIRS include
#  LIBRARIES fusion2urdf
)

include_directories(
# include
  ${catkin_INCLUDE_DIRS}
)

