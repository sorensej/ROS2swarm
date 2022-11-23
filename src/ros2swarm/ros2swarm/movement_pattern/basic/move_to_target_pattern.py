#!/usr/bin/env python3
#    Copyright 2020 Marian Begemann
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

from geometry_msgs.msg import Twist, Pose
from ros2swarm.utils import setup_node, quaternion_transform
from ros2swarm.movement_pattern.movement_pattern import MovementPattern
from gazebo_msgs.msg import ModelStates
import numpy as np

class MoveToTargetPattern(MovementPattern):
    """
    Pattern to move to a target point defined in global coordinates
    
    *Either:
    	set gotolocation to true and specify the coordinates 
    *OR:
    	combine in code by using the following topics

    	To use: publish on the /target_pose topic the pose of the target point and on the /robot_pose topic the position of the robot

    	To stop moving: publish the same pose on both topics

    pattern_node >> publishing to the self.get_namespace()/drive_command topic
    """

    def __init__(self):
        """Initialize the move_to_target pattern node."""
        super().__init__('move_to_target_pattern')
        self.declare_parameters(
            namespace='',
            parameters=[
                ('timer_period', None)
            ])

        timer_period = float(
            self.get_parameter("timer_period").get_parameter_value().double_value)
        self.gotolocation = 'false' #set to true if want to go to specific location
        self.target_pose = Pose()
        self.robot_pose = Pose()
        self.msg = Twist()
        self.timer = self.create_timer(timer_period, self.swarm_command_controlled_timer(self.timer_callback))
        #to ease the implementation of movement, absolute positioning is used
        #we can access the pose of all objects in simulation with this
        if(self.gotolocation=='true'): 
            #self.get_logger().info('Comes to go to location')
            self.model_states = ModelStates()
            self.target_pose.position.x = -5.0  #specify coordinate x
            self.target_pose.position.y = -5.0	 #specify coordinate y
            self.subscription_models_states = self.create_subscription(ModelStates, '/model_states/model_states', self.model_states_callback, 10)
        else:
            #self.get_logger().info('Comes to go to task alloc')
            self.target_pose_subscription = self.create_subscription(Pose, self.get_namespace() + '/target_pose', self.target_pose_callback, 10)
            self.robot_pose_subscription = self.create_subscription(Pose, self.get_namespace() + '/robot_pose', self.robot_pose_callback, 10)
            
            
    def model_states_callback(self, msg):
        # the global position of robots
        self.model_states = msg
        indices = [i for i, x in enumerate(self.model_states.name) if "robot_name_" in x]
        for i in indices:
            if(self.get_namespace()[-1] == self.model_states.name[i][-1]):
                self.robot_pose = self.model_states.pose[i]
        if(self.robot_pose != self.target_pose):
        	self.update_speeds()
                
    def target_pose_callback(self, pose):
        if(self.target_pose != pose):
        	self.target_pose = pose
        	self.update_speeds()

    def robot_pose_callback(self, pose):
        if(self.robot_pose != pose):
            self.robot_pose = pose
            self.update_speeds()

    def timer_callback(self):
        self.command_publisher.publish(self.msg)

    def update_speeds(self):
        vector_x = self.target_pose.position.x - self.robot_pose.position.x
        vector_y = self.target_pose.position.y - self.robot_pose.position.y
        if(vector_x == 0 and vector_y == 0):
            self.msg.linear.x = 0.0
            self.msg.linear.y = 0.0
            self.msg.angular.z = 0.0
            return

        self.msg.linear.x = 0.0
        self.msg.linear.y = 0.0
        #computing the angle
        if(vector_x >= 0):
            theta = np.arctan((self.target_pose.position.y - self.robot_pose.position.y) / (self.target_pose.position.x - self.robot_pose.position.x))
        if(vector_x < 0 and vector_y >0):
            theta = 3.1415 + np.arctan((self.target_pose.position.y - self.robot_pose.position.y) / (self.target_pose.position.x - self.robot_pose.position.x))
        if(vector_x < 0 and vector_y <0):
            theta = -3.1415 + np.arctan((self.target_pose.position.y - self.robot_pose.position.y) / (self.target_pose.position.x - self.robot_pose.position.x))
        t_x,t_y,t_z = quaternion_transform.euler_from_quaternion(self.robot_pose.orientation)

        delta = theta - t_z
        if(delta > 3.1415):
            delta = delta - 2*3.1415
        if(delta < -3.1415):
            delta = delta + 2*3.1415
        if(delta < 0): #for normal angles
            self.msg.angular.z = -0.4
        if(delta > 0):
            self.msg.angular.z = 0.4
        if(delta < 3.1415/4 and delta > -3.1415/4): #for small angles
            self.msg.linear.x = 1.0
            self.msg.angular.z = self.msg.angular.z/2


def main(args=None):
    """Create a node for the move_to_target pattern and handle the setup."""
    setup_node.init_and_spin(args, MoveToTargetPattern)


if __name__ == '__main__':
    main()