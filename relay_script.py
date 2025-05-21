from gpiozero import LED
from time import sleep
import middle_level.symovo_lib as symovo_lib
import middle_level.igus_lib as igus_lib
import middle_level.robot_lib as robot_lib
import low_level.xarm_positions as xarm_positions

relay = LED(17)

timer_out = 5
timer = 0


while True:
    try:
        sleep(1)
        if timer > timer_out:
            timer = 0
            if relay.is_active:
                if symovo_lib.agv_on_charging():
                    robot_lib.go_to_position(xarm_positions.poses["TRANSPORT_STEP_1"],xarm_positions.poses["TRANSPORT_STEP_2"],angle_speed=20)
                    igus_lib.go_to_position(0,5000, reconfig=True, wait=True)
                    relay.off()
            else:
                if symovo_lib.agv_on_charging() == False:
                    relay.on()
        timer = timer + 1
    except:
        continue
