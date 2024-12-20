#!/usr/bin/env python3  

import rospy  
from geometry_msgs.msg import Twist, PoseStamped 
from std_msgs.msg import Float32 
from sensor_msgs.msg import LaserScan   #Lidar 
import numpy as np 

#This class will make the puzzlebot move to a given goal 
class GoToGoal():  
    def __init__(self):  
        rospy.on_shutdown(self.cleanup)

        ############ ROBOT CONSTANTS ################  

        self.r = 0.05 #wheel radius [m] 
        self.L = 0.19 #wheel separation [m] 

        ############ Variables ############### 

        self.x = 0.0 #x position of the robot [m] 
        self.y = 0.0 #y position of the robot [m] 
        self.theta = 0.0 #angle of the robot [rad] 

        ############ Variables ############### 

        self.x_target = 0.0 #x position of the goal 
        self.y_target = 0.0 #y position of the goal 
        self.goal_received = 0  #flag to indicate if the goal has been received 
        self.lidar_received = 0 #flag to indicate if the laser scan has been received 
        self.target_position_tolerance = 0.10 #acceptable distance to the goal to declare the robot has arrived to it [m] 
        fw_distance = 0.3 #0.4
        self.integral = 0.0
        self.prev_error = 0.0
        stop_distance = 0.001 # distance from closest obstacle to stop the robot [m] 
        eps = 0.20 #Fat guard epsilon 
        v_msg = Twist() #Robot's desired speed  
        self.wr = 0 #right wheel speed [rad/s] 
        self.wl = 0 #left wheel speed [rad/s] 
        self.current_state = 'GoToGoal' #Robot's current state 

        ###******* INIT PUBLISHERS *******###  

        self.pub_cmd_vel = rospy.Publisher('/puzzlebot_1/base_controller/cmd_vel', Twist, queue_size=1)  

        ############################### SUBSCRIBERS #####################################  

        rospy.Subscriber("puzzlebot_1/wl", Float32, self.wl_cb)  
        rospy.Subscriber("puzzlebot_1/wr", Float32, self.wr_cb)  
        rospy.Subscriber("puzzlebot_goal", PoseStamped, self.goal_cb) 
        rospy.Subscriber("puzzlebot_1/scan", LaserScan, self.laser_cb) 

        #********** INIT NODE **********###  
        freq = 20 
        rate = rospy.Rate(freq) #freq Hz  
        dt = 1.0/float(freq) #Dt is the time between one calculation and the next one 
        fwf = True
        d_t1 = 0.0
        d_t = 0.0
        theta_ao = 0.0
        theta_gtg = 0.0

        ################ MAIN LOOP ################  
        while not rospy.is_shutdown():
            self.update_state(self.wr, self.wl, dt) #update the robot's state 

            if self.lidar_received:
                closest_range, closest_angle = self.get_closest_object(self.lidar_msg) #get the closest object range and angle 

                if self.current_state == 'Stop': 
                    if self.goal_received: 
                        print("Change to Go To Goal from stop") 
                        self.current_state = "GoToGoal" 
                        self.goal_received=0 

                    else: 
                        v_msg.linear.x = 0.0 
                        v_msg.angular.z = 0.0 

                elif self.current_state == 'GoToGoal':  
                    if self.at_goal() or  closest_range <  stop_distance:  
                        print("Change to Stop from Go to goal") 
                        print(self.x_target)
                        print(self.y_target)
                        self.current_state = "Stop"  

                    elif closest_range < fw_distance: 
                        print("Change to wall following from Go to goal") 
                        self.current_state= "WallFollower" 

                    else:        
                        v_gtg, w_gtg = self.compute_gtg_control(self.x_target, self.y_target, self.x, self.y, self.theta)   
                        v_msg.linear.x = v_gtg 
                        v_msg.angular.z = w_gtg      

                elif self.current_state == 'WallFollower': 
                    theta_gtg, theta_ao = self.compute_angles(self.x_target, self.y_target, self.x, self.y, self.theta, closest_angle)
                    d_t = np.sqrt((self.x_target-self.x)**2+(self.y_target-self.y)**2)
                    print("Quit?: ",self.leave_fw(theta_gtg, theta_ao, d_t, d_t1))

                    if self.at_goal() or closest_range < stop_distance: 
                        print("Change to Stop") 
                        self.current_state = "Stop" 
                        fwf = True

                    elif self.leave_fw(theta_gtg, theta_ao, d_t, d_t1):
                        print("Change to Go to goal from wall follower") 
                        self.current_state = "GoToGoal" 
                        fwf = True

                    else:
                        d_t1 = np.sqrt((self.x_target-self.x)**2+(self.y_target-self.y)**2)  if fwf else d_t1
                        clk_cnt = self.clockwise_counter(self.x_target, self.y_target, self.x, self.y, self.theta, closest_angle) if fwf else clk_cnt
                        fwf = False
                        v_wf, w_wf =self.fw_controller(closest_angle, clk_cnt) 
                        v_msg.linear.x = v_wf
                        v_msg.angular.z = w_wf 


            self.pub_cmd_vel.publish(v_msg)  

            rate.sleep()  

     

    def at_goal(self): 
        #This function returns true if the robot is close enough to the goal 
        #This functions receives the goal's position and returns a boolean 
        #This functions returns a boolean 

        return np.sqrt((self.x_target-self.x)**2+(self.y_target-self.y)**2)<self.target_position_tolerance 

    def get_closest_object(self, lidar_msg): 
        min_idx = np.argmin(lidar_msg.ranges) 
        closest_range = lidar_msg.ranges[min_idx] 
        closest_angle = lidar_msg.angle_min + min_idx * lidar_msg.angle_increment 
        closest_angle = np.arctan2(np.sin(closest_angle), np.cos(closest_angle)) 

        return closest_range, closest_angle

    def compute_gtg_control(self, x_target, y_target, x_robot, y_robot, theta_robot): 
        #This function returns the linear and angular speed to reach a given goal 
        #This functions receives the goal's position (x_target, y_target) [m] 
        #  and robot's position (x_robot, y_robot, theta_robot) [m, rad] 
        #This functions returns the robot's speed (v, w) [m/s] and [rad/s] 

        kvmax = 0.2 #linear speed maximum gain  
        kwmax = 1.0 #angular angular speed maximum gain 

        av = 1.0 #Constant to adjust the exponential's growth rate   
        aw = 2.0 #Constant to adjust the exponential's growth rate 

        ed = np.sqrt((x_target-x_robot)**2+(y_target-y_robot)**2) 

        #Compute angle to the target position 

        theta_target = np.arctan2(y_target-y_robot,x_target-x_robot) 
        e_theta = theta_target-theta_robot 

        #limit e_theta from -pi to pi 
        #This part is very important to avoid abrupt changes when error switches between 0 and +-2pi 
        e_theta = np.arctan2(np.sin(e_theta), np.cos(e_theta)) 
        #Compute the robot's angular speed 
        kw = kwmax*(1-np.exp(-aw*e_theta**2))/abs(e_theta) #Constant to change the speed  
        w = kw*e_theta 

        if abs(e_theta) > np.pi/8: 
            #we first turn to the goal 
            v = 0 #linear speed  

        else: 
            # Make the linear speed gain proportional to the distance to the target position 
            kv = kvmax*(1-np.exp(-av*ed**2))/abs(ed) #Constant to change the speed  
            v = kv*ed #linear speed  

        return v, w

    def clockwise_counter(self, x_target, y_target, x_robot, y_robot, theta_robot, closest_angle):
        theta_target=np.arctan2(y_target-y_robot,x_target-x_robot) 
        e_theta=theta_target-theta_robot
        e_theta = np.arctan2(np.sin(e_theta), np.cos(e_theta)) 

        theta_ao = closest_angle
        theta_ao = np.arctan2(np.sin(theta_ao), np.cos(theta_ao))

        theta_ao = theta_ao - np.pi
        theta_ao = np.arctan2(np.sin(theta_ao), np.cos(theta_ao))

        theta_fw = -np.pi/2 + theta_ao
        theta_fw = np.arctan2(np.sin(theta_fw), np.cos(theta_fw))
    
        if np.abs(theta_fw - e_theta) <= np.pi/2:
            return 1
        else:
            return 0
        
    def compute_angles(self, x_target, y_target, x_robot, y_robot, theta_robot, closest_angle):
        theta_target=np.arctan2(y_target-y_robot,x_target-x_robot) 
        e_theta=theta_target-theta_robot
        e_theta = np.arctan2(np.sin(e_theta), np.cos(e_theta)) 

        theta_ao = closest_angle
        theta_ao = np.arctan2(np.sin(theta_ao), np.cos(theta_ao))

        theta_ao = theta_ao - np.pi
        theta_ao = np.arctan2(np.sin(theta_ao), np.cos(theta_ao))

        return e_theta, theta_ao
    
    def fw_controller(self, closest_angle, counter_clockwise):
        theta_ao = closest_angle
        theta_ao = np.arctan2(np.sin(theta_ao), np.cos(theta_ao))

        theta_ao = theta_ao - np.pi
        theta_ao = np.arctan2(np.sin(theta_ao), np.cos(theta_ao))

        theta_fw = -np.pi/2 + theta_ao if counter_clockwise else np.pi/2 + theta_ao
        theta_fw = np.arctan2(np.sin(theta_fw), np.cos(theta_fw))

        w_fw = 2.0 * theta_fw
        v_fw = 0.09
    
        return v_fw, w_fw
    
    def leave_fw(self, theta_gtg, theta_ao, d_t, d_t1):
        print("D(h1): ", d_t1)
        print("D: ", d_t)
        print("Clear? : ", np.abs(theta_ao - theta_gtg))
        print()
        if (d_t < d_t1) and (np.abs(theta_ao - theta_gtg) < np.pi/2):
            return True
        else:
            return False

    def laser_cb(self, msg):   
        ## This function receives a message of type LaserScan   
        self.lidar_msg = msg  
        self.lidar_received = 1  

    def wl_cb(self, wl):  
        ## This function receives a the left wheel speed [rad/s] 
        self.wl = wl.data 

    def wr_cb(self, wr):  
        ## This function receives a the right wheel speed.  
        self.wr = wr.data  

    def goal_cb(self, goal):  
        ## This function receives a the goal from rviz.  
        print("Goal received") 
        # assign the goal position 
        self.x_target = goal.pose.position.x 
        self.y_target = goal.pose.position.y 

        self.goal_received=1 

    def update_state(self, wr, wl, delta_t): 
        #This function updates the robot's state 
        #This functions receives the wheel speeds wr and wl in [rad/sec]  
        # and returns the robot's state 

        v = self.r *(wr+wl) / 2 
        w = self.r *(wr-wl) / self.L        

        self.theta = self.theta + w * delta_t 

        #Crop theta_r from -pi to pi 
        self.theta = np.arctan2(np.sin(self.theta), np.cos(self.theta)) 

        vx = v * np.cos(self.theta) 
        vy = v * np.sin(self.theta) 

        self.x = self.x + vx * delta_t  
        self.y = self.y + vy * delta_t 


    def cleanup(self):  
        #This function is called just before finishing the node  
        # You can use it to clean things up before leaving  
        # Example: stop the robot before finishing a node.    

        vel_msg = Twist() 
        self.pub_cmd_vel.publish(vel_msg) 

############################### MAIN PROGRAM ####################################  

if __name__ == "__main__":  
    rospy.init_node("gtg_obstacles", anonymous=True)  
    GoToGoal()
