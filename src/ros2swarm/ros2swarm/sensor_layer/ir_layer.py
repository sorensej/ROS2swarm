#!/usr/bin/env python3
#    Copyright 2020 Josephine Brauer, Tanja Kaiser
#
#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.
import functools
import rclpy

from rclpy.node import Node
from ros2swarm.utils import setup_node
from sensor_msgs.msg import Range
from communication_interfaces.msg import RangeData, RayArray, RobotArray, Ray
from rclpy.qos import qos_profile_sensor_data

class IRLayer(Node):
    """
    Subscribe to a variable number of Range topics. The topics can be
    specified in ros2swarm/config/robot/sensor_specification.yaml.
    
    Determine and publish a RangeData message on topic /range_data
    based on the received sensor messages.
    
    Determine and publish the rays indicating an obstacle and for
    each obstacle the center ray for the current ranges.

    IRLayer >> HardwareProtectionLayer >> publish twist message
    or
    IRLayer >> pattern_node >> HardwareProtectionLayer
    >> publish twist message
    """

    def __init__(self):
        """Initialize the node."""
        super().__init__('ir_layer') 
        
        # declare paramters
        self.declare_parameters(
            namespace='',
            parameters=[
                ('angles', None),
                ('range_topics', None),
                ('max_range', None),
                ('min_range', None),
            ])
            
        # get the parameter values from sensor_specifications file
        self.angles = self.get_parameter(
            "angles").get_parameter_value().double_array_value
        self.range_topics = self.get_parameter(
            "range_topics").get_parameter_value().string_array_value 
        self.param_max_range = float(
            self.get_parameter("max_range").get_parameter_value().double_value)
        self.param_min_range = self.get_parameter(
            "min_range").get_parameter_value().double_value
            
        # other class variables
        self.current_ranges = [None] * len(self.range_topics)
        
        # publishers and subscribers of sensor topics
        self.range_subscriptions = [self.create_subscription(
                                       Range,
                                       self.get_namespace() + "/" + self.range_topics[i],
                                       functools.partial(self.range_callback, index=i),
                                       qos_profile=qos_profile_sensor_data)
                                       for i in range(len(self.range_topics))]
        
        # publisher for range data
        self.range_data_publisher = self.create_publisher(
            RangeData,
            self.get_namespace() + '/range_data',
            100)
        
        # publisher for obstacles
        self.robot_publisher = self.create_publisher(
            RobotArray,
            self.get_namespace() + '/robots',
            100)

    def range_callback(self, range_msg, index):
        """
        Save the range in the array of current ranges and get the angle
        between the corresponding ray and the x-axis of the robot from
        the specifications file.

        Publish a RangeData message on basis of the current ranges, if
        at least one range measurement has already been received from
        each sensor.
        """
        
        # saves the received range
        self.current_ranges[index] = range_msg.range
        
        # publishes a range data message and detects the robots in the
        # ranges
        if not None in self.current_ranges:
            msg = RangeData()
            msg.header = range_msg.header
            msg.header.frame_id = ""
            msg.ranges = self.current_ranges
            msg.angles = self.angles
            self.range_data_publisher.publish(msg)
            self.publish_robots(msg.header)
            self.current_ranges = [None] * len(self.range_topics)
            
    def publish_robots(self, header):
        """Identify all ranges that contain robots, based on the
        settings in the pattern parameters.

        :return: return the list of all found robots and a list in
        which each robot is represented by a single ray. In case of the
        IR Layer, they are the same.
        """
        
        # array of robots defined by the rays of the sensors that 
        # detect them
        robots_msg = RobotArray()  
        robots_msg.header = header
        # assume a robot in the direction of each ray that detects
        # an object
        for i in range(len(self.current_ranges)):
            if self.param_min_range < self.current_ranges[i] < self.param_max_range:
                temp_robot = RayArray()
                temp_robot.header = header
                temp_ray = Ray()
                temp_ray.header = header
                temp_ray.length = self.current_ranges[i]
                temp_ray.angle = self.angles[i]
                temp_robot.rays.append(temp_ray)
                robots_msg.robots.append(temp_robot)
                robots_msg.rays.append(temp_ray)
        # send response
        self.robot_publisher.publish(robots_msg)
        self.get_logger().error('Found "{}" robots'.format(len(robots_msg.robots)))

def main(args=None):
    """
    Create a node for the IR Layer, spin it and handle the
    destruction.
    """
    setup_node.init_and_spin(args, IRLayer)


if __name__ == '__main__':
    main()
