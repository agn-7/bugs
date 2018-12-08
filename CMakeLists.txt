cmake_minimum_required(VERSION 2.8.3)
project(bugs)


# Set the build type.  Options are:
#  Coverage       : w/ debug symbols, w/o optimization, w/ code-coverage
#  Debug          : w/ debug symbols, w/o optimization
#  Release        : w/o debug symbols, w/ optimization
#  RelWithDebInfo : w/ debug symbols, w/ optimization
#  MinSizeRel     : w/o debug symbols, w/ optimization, stripped binaries
#set(ROS_BUILD_TYPE RelWithDebInfo)

find_package(catkin REQUIRED COMPONENTS
  geometry_msgs
  rospy
  roscpp
  sensor_msgs
  std_msgs
  laser_geometry
  roslib
  tf
  nav_msgs
  gazebo_msgs
)

generate_messages(
  DEPENDENCIES
  geometry_msgs  sensor_msgs  std_msgs gazebo_msgs nav_msgs
)


catkin_package(
CATKIN_DEPENDS geometry_msgs rospy roscpp laser_geometry roslib sensor_msgs std_msgs tf gazebo_msgs nav_msgs
)


###########
## Build ##
###########

## Specify additional locations of header files
## Your package locations should be listed before other locations
# include_directories(include)
include_directories(
  ${catkin_INCLUDE_DIRS}
)


 install(PROGRAMS
   scripts/*.py
   DESTINATION ${CATKIN_PACKAGE_BIN_DESTINATION}
)

