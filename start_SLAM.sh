# start SLAM for the simulation
 ROS_DOMAIN_ID=42 ros2 launch cslam_experiments cslam_lidar.launch.py max_nb_robots:=3 namespace:=/r0 robot_id:=0
 ROS_DOMAIN_ID=42 ros2 launch cslam_experiments cslam_lidar.launch.py max_nb_robots:=3 namespace:=/r1 robot_id:=1
 ROS_DOMAIN_ID=42 ros2 launch cslam_experiments cslam_lidar.launch.py max_nb_robots:=3 namespace:=/r2 robot_id:=2
 ROS_DOMAIN_ID=42 ros2 launch cslam_experiments remapper.launch.py real_robot_id:="'robot_name_0'" cslam_robot_id:="'r0'"
 ROS_DOMAIN_ID=42 ros2 launch cslam_experiments remapper.launch.py real_robot_id:="'robot_name_1'" cslam_robot_id:="'r1'"
 ROS_DOMAIN_ID=42 ros2 launch cslam_experiments remapper.launch.py real_robot_id:="'robot_name_2'" cslam_robot_id:="'r2'"
 ROS_DOMAIN_ID=42 ros2 launch cslam_visualization visualization_lidar.launch.py 
 