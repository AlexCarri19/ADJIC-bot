#!/usr/bin/env python3
import rospy
import movements as mv
from robot_place import Xarm_place

class Xarm_pick(Xarm_place): 

    def execute(self , pallets , home , observation):
        try:
            rospy.sleep(2)
            pallets_r , aruco = self.get_pallets()
            for pallet_r , pallet in zip(pallets_r , pallets):
                self.control_gripper("open")
                rospy.sleep(1)

                print("Pallet")
                self.move_to_pose(pallet_r["type"] , pallet_r["pose"])
                #rospy.sleep(3)

                self.control_gripper("close")
                rospy.sleep(3)

                print("To pallet")
                self.execute_sequence(pallet)

                print("Home")
                self.move_to_pose(home["type"] , home["pose"])
                #rospy.sleep(3)
                    
            print("Observation")
            self.move_to_pose(observation["type"] , observation["pose"])
            #rospy.sleep(8)

            self.at_pick = False
                    
            return True

        except:
            print("Robot no iniciado")
            return None
        
    def execute(self , pallets , home , observation):
        self.execute_sequence(mv.pi_full)

    def execute_condition(self):
        return self.at_pick
        
############################### PROGRAMA PRINCIPAL ####################################
if __name__ == "__main__": 
    rospy.init_node("pick_xarm") 
    Xarm_pick(mv.pi_pallets , mv.pi_observation , mv.pi_home , 132)