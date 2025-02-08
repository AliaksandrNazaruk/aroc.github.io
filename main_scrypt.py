import requests
import time
import symovo_lib
import robot_lib
import igus_lib
import xarm_positions
import led_lib
from Regal import Regal, Shelf

regal = Regal('Rack1')
regal.add_shelf(Shelf(32, []))
regal.add_shelf(Shelf(53, []))
regal.add_shelf(Shelf(42, ["Corn", "Bio", "Sonax"]))
regal.add_shelf(Shelf(32, ["Crackers", "Rice", "Pringles", "Dishwash"]))
regal.add_shelf(Shelf(32, ["Filets", "Speise Green", "Speise Red", "Tea"]))

def job(item_data,speed):
    if speed>100:
        speed = 100
    x = item_data['x']
    section = item_data['section_index']
    y = item_data['y']
    ground_zero = 42
    zero_readypos = 35
    move_val = y-ground_zero-zero_readypos

    symovo_lib.go_to_position("GoTo"+item_data['regal_name'], reconfig=True, wait=True)
    igus_lib.go_to_position(move_val,speed*100, reconfig=True, wait=True)
    robot_lib.go_to_position(xarm_positions.poses["READY_STEP_1"],
                             xarm_positions.poses["READY_STEP_2"],
                             xarm_positions.poses["READY_SECTION_"+str(section)],
                             angle_speed=speed)
    
def start_job_with_name(name):
    item = regal.find_item(name)
    if item is not None:
        coords = regal.get_coordinates(item)
        data = item|coords
        job(data,20)
        return True
    return False

# start_job_with_name("Sonax")

# led_lib.send_to_arduino(3),robot_lib.go_to_position(xarm_positions.poses["READY_STEP_1"],xarm_positions.poses["READY_STEP_2"],angle_speed=40),led_lib.send_to_arduino(1)
# time.sleep(2)
# led_lib.send_to_arduino(3),robot_lib.go_to_position(xarm_positions.poses["READY_STEP_1"],xarm_positions.poses["READY_STEP_2"],xarm_positions.poses["READY_SECTION_"+str(2)],angle_speed=40),led_lib.send_to_arduino(1)
# time.sleep(2)
# led_lib.send_to_arduino(3),robot_lib.go_to_position(xarm_positions.poses["READY_STEP_1"],xarm_positions.poses["READY_STEP_2"],xarm_positions.poses["READY_SECTION_"+str(3)],angle_speed=40),led_lib.send_to_arduino(1)
# time.sleep(2)
# led_lib.send_to_arduino(3),robot_lib.go_to_position(xarm_positions.poses["READY_STEP_1"],xarm_positions.poses["READY_STEP_2"],xarm_positions.poses["READY_SECTION_"+str(4)],angle_speed=40),led_lib.send_to_arduino(1)
# time.sleep(2)
# led_lib.send_to_arduino(3), igus_lib.go_to_position(7,1000, reconfig=True, wait=True),led_lib.send_to_arduino(1)
# led_lib.send_to_arduino(3),robot_lib.go_to_position(xarm_positions.poses["READY_STEP_1"],xarm_positions.poses["READY_STEP_2"],angle_speed=50),led_lib.send_to_arduino(1)
# led_lib.send_to_arduino(3),robot_lib.go_to_position(xarm_positions.poses["TRANSPORT_STEP_1"],xarm_positions.poses["TRANSPORT_STEP_2"],angle_speed=5),led_lib.send_to_arduino(1)
# while True:
    # led_lib.send_to_arduino(3),robot_lib.go_to_position(xarm_positions.poses["READY_STEP_1"],xarm_positions.poses["READY_STEP_2"],xarm_positions.poses["READY_SECTION_"+str(1)],angle_speed=40),led_lib.send_to_arduino(1)
    # time.sleep(2)
    # led_lib.send_to_arduino(3),robot_lib.go_to_position(xarm_positions.poses["READY_STEP_1"],xarm_positions.poses["READY_STEP_2"],xarm_positions.poses["READY_SECTION_"+str(2)],angle_speed=40),led_lib.send_to_arduino(1)
    # time.sleep(2)
    # led_lib.send_to_arduino(3),robot_lib.go_to_position(xarm_positions.poses["READY_STEP_1"],xarm_positions.poses["READY_STEP_2"],xarm_positions.poses["READY_SECTION_"+str(3)],angle_speed=40),led_lib.send_to_arduino(1)
    # time.sleep(2)
    # led_lib.send_to_arduino(3),robot_lib.go_to_position(xarm_positions.poses["READY_STEP_1"],xarm_positions.poses["READY_STEP_2"],xarm_positions.poses["READY_SECTION_"+str(4)],angle_speed=40),led_lib.send_to_arduino(1)
    # time.sleep(2)
    # led_lib.send_to_arduino(3), symovo_lib.go_to_position("GoToRack2", reconfig=True, wait=True),led_lib.send_to_arduino(1)
    # led_lib.send_to_arduino(3), igus_lib.go_to_position(13,14000000, reconfig=True, wait=True),led_lib.send_to_arduino(1)
    # led_lib.send_to_arduino(3),robot_lib.go_to_position(xarm_positions.poses["READY_STEP_1"],xarm_positions.poses["READY_STEP_2"],angle_speed=100),led_lib.send_to_arduino(1)
    # time.sleep(5)

    # led_lib.send_to_arduino(3), symovo_lib.go_to_position("GoToRack1", reconfig=True, wait=True),led_lib.send_to_arduino(1)
    # led_lib.send_to_arduino(3), igus_lib.go_to_position(7,4000, reconfig=True, wait=True),led_lib.send_to_arduino(1)
    # led_lib.send_to_arduino(3), robot_lib.go_to_position(xarm_positions.poses["READY_STEP_1"],xarm_positions.poses["READY_STEP_2"],angle_speed=100),led_lib.send_to_arduino(1)
    # time.sleep(5)







# while True:

#     led_lib.send_to_arduino(3), symovo_lib.go_to_position("GoToRack1", reconfig=True, wait=True),led_lib.send_to_arduino(1)
#     time.sleep(5)
#     led_lib.send_to_arduino(3), igus_lib.go_to_position(20,2000, reconfig=True, wait=True),led_lib.send_to_arduino(1)
#     led_lib.send_to_arduino(3), symovo_lib.go_to_position("GoToRack2", reconfig=True, wait=True),led_liG4b.send_to_arduino(1)
#     time.sleep(5)
#     led_lib.send_to_arduino(3), igus_lib.go_to_position(0,2000, reconfig=True, wait=True),led_lib.send_to_arduino(1)
#     led_lib.send_to_arduino(3),robot_lib.go_to_position(xarm_positions.poses["READY_STEP_1"],xarm_positions.poses["READY_STEP_2"],angle_speed=40),led_lib.send_to_arduino(1)
#     time.sleep(5)
#     led_lib.send_to_arduino(3), symovo_lib.go_to_position("Presentation", reconfig=True, wait=True),led_lib.send_to_arduino(1)
#     time.sleep(5)
#     led_lib.send_to_arduino(3), igus_lib.go_to_position(20,500, reconfig=True, wait=False),led_lib.send_to_arduino(1)


# result = send_to_webserver( "get_depth_value", "/start/xarm_script",_data=_data)
# print(result)
# result = send_to_webserver( "take", "/start/xarm_script",_data=result)

# result = send_to_webserver( "measure", "/start/xarm_script",_data=_data)

# print(result)
# camera_offset_z = -22
# camera_offset_y = -35
# camera_offset_x = 50
# _data = {
#     "correct_position": False,
#     "z" : result["depth"]+camera_offset_z,
#     "y" : 0+camera_offset_y,
#     "x" : 0+camera_offset_x,
#     "w":result["width"],
#     "h":result["heigth"]
# }
# send_to_webserver( "take_to_box", "/start/xarm_script",_data=_data)


# while True:
#     create_transport_from_job(second_job)
#     send_to_igus("ABS", value=30, velocity=3000, wait=True)
#     send_to_igus("ABS", value=0, velocity=3000, wait=True)
#     time.sleep(5)
#     create_transport_from_job(first_job)
#     send_to_webserver("GET","xarm_script")
#     count = count+1
#     print("Cycle: "+str(count))

