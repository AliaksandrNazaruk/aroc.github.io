import requests
import time
import threading
from core.state import xarm_client, igus_client

import drivers.xarm_scripts.xarm_positions as xarm_positions
import services.led_lib as led_lib
from core.configuration import (
    default_speed,
    ground_zero,
    zero_readypos,
    tcp_speed,
    tcp_acceleration,
    angle_speed,
    angle_acceleration
)
from core.state import symovo_car
import logging

logger = logging.getLogger(__name__)

async def script_operator(stop_event, data):
    """
    Execute robot script based on command.
    
    Args:
        stop_event: Event to signal script termination
        command: Command to execute
    """
    command = data['command']
    try:
        if command == "box_1":
            await goToBox1(stop_event)
        elif command == "box_2":
            await goToBox2(stop_event)
        elif command == "transport":
            await transport_position(stop_event)
        elif "change_position" == command:
            await changePosition(stop_event, data['position_name'],speed=int(data['speed']))

        elif command == "show_script":
            await show_script(speed = 90)
        elif command == "show_script2":
            await show_script2(speed = 70)
    except Exception as e:
        logger.error(f"Script operator error: {e}")

async def show_script(speed = default_speed):
    try:
        async with xarm_client as client:
            robot_result = await client.go_to_position([xarm_positions.poses["READY_STEP_1"],xarm_positions.poses["READY_STEP_2"],xarm_positions.poses["READY_SECTION_CENTER"],xarm_positions.poses["TARGET_DAVE_CAMERA_FOCUS"]],angle_speed=speed)
        if not robot_result.get('success', False):
            logger.error(f"Robot movement failed: {robot_result.get('error')}")
    except Exception as e:
        logger.error(f"Change position error: {e}")
    
async def show_script2(speed = default_speed):
    try:
        symovo_result = symovo_car.go_to_position("GoToRegal", reconfig=True, wait=True)
        time.sleep(10)
            # Move igus motor
        igus_result = await command_interface.execute_command(
            MotorCommand(
                type="move_to_position",
                params={
                    "position": 45000,
                    "velocity": speed * 100,
                    "acceleration": speed * 100,
                    "wait": False
                }
            )
        )
        robot_result = robot_lib.go_to_position([xarm_positions.poses["READY_STEP_1"],
                                                xarm_positions.poses["READY_STEP_2"],
                                                xarm_positions.poses["READY_SECTION_CENTER"],
                                                xarm_positions.poses["TARGET_DAVE_CAMERA_FOCUS"]],
                                                angle_speed=speed)
        if not robot_result.get('success', False):
            logger.error(f"Robot movement failed: {robot_result.get('error')}")

    except Exception as e:
        logger.error(f"Change position error: {e}")

async def job(item_data, speed = default_speed):
    """
    Execute a single job with given item data.
    
    Args:
        item_data: Dictionary containing job parameters
    """
    try:
        y = item_data['sectionHeight']
        move_val = y-(ground_zero+zero_readypos)

        # Move to source position
        symovo_result = symovo_car.go_to_position("GoTo"+item_data['sourceCoordinate'], reconfig=True, wait=True)
        if not symovo_result.get('success', False):
            logger.error(f"Symovo movement failed: {symovo_result.get('error')}")
            return False

        # Move igus motor
        igus_result = await command_interface.execute_command(
            MotorCommand(
                type="move_to_position",
                params={
                    "position": move_val*1000,
                    "velocity": tcp_speed * 50,
                    "acceleration": tcp_acceleration,
                    "wait": True
                }
            )
        )
        if not igus_result.get('success', False):
            logger.error(f"Igus movement failed: {igus_result.get('error')}")
            return False

        return True
    except Exception as e:
        logger.error(f"Job execution error: {e}")
        return False

def start_job_with_name(item):
    if item is not None:
        for i in range(item["quantityToMove"]):
            if not job(item):
                return False
        return True
    return False

async def transport_position(stop_event, speed=default_speed):
    try:
        async with igus_client as _igus_client:
            igus_result = await _igus_client.move_to_position(position=20000,velocity=speed * 100,acceleration=speed * 100,wait=True)
            if igus_result.get('success', False):
                async with xarm_client as client:
                    current_pose = await client.get_current_position()
                    if current_pose[0] != "TRANSPORT_STEP_2":
                        await client.go_to_position([xarm_positions.poses["TRANSPORT_STEP_1"], xarm_positions.poses["TRANSPORT_STEP_2"]],angle_speed=speed)
                    igus_result2 = await _igus_client.move_to_position(position=0,velocity=speed * 100,acceleration=speed * 100,wait=True)
                    if igus_result2.get('success', False):
                        return True
        raise Exception("Transport position failed")
    except Exception as e:
        logger.error(f"Transport position error: {e}")
        return False

async def goToBox1(stop_event, speed = default_speed):
    first_pos = 40000
    second_pos = 30000
    try:
        async with igus_client as _igus_client:
            igus_result = await _igus_client.move_to_position(first_pos,(speed * 100),(speed * 100),True)
            igus_position = await igus_client.get_position()
            igus_position = igus_position.get('position')
            result = abs(igus_position - first_pos)
            if  result < 250:
                async with xarm_client as _xarm_client:
                    current_pose = await _xarm_client.get_current_position()
                    igus_result = await _igus_client.move_to_position(second_pos,(speed * 100)/3,(speed * 100)/2,False)

                    if not igus_result.get('success', False):
                        logger.error(f"Igus movement failed: {igus_result.get('error')}")
                        return False
                                                            
                    robot_result = await _xarm_client.go_to_position([xarm_positions.poses["TRANSPORT_STEP_1"], xarm_positions.poses["BOX_STEP_1"], xarm_positions.poses["BOX_1_STEP_2"]],angle_speed=speed)

                    if not robot_result.get('success', False):
                        logger.error(f"Robot movement failed: {robot_result.get('error')}")
                        return False
                    
                    return True
                
    except Exception as e:
        logger.error(f"Go to box 1 error: {e}")
        return e

async def goToBox2(stop_event, speed = default_speed):
    first_pos = 40000
    second_pos = 30000
    try:
        async with igus_client as _igus_client:
            igus_result = await _igus_client.move_to_position(first_pos,(speed * 100),(speed * 100),True)
            igus_position = await igus_client.get_position()
            igus_position = igus_position.get('position')
            result = abs(igus_position - first_pos)
            if  result < 250:
                async with xarm_client as _xarm_client:
                    current_pose = await _xarm_client.get_current_position()
                    igus_result = await _igus_client.move_to_position(30000,(speed * 100)/3,(speed * 100)/2,False)

                    if not igus_result.get('success', False):
                        logger.error(f"Igus movement failed: {igus_result.get('error')}")
                        return False

                    robot_result = await _xarm_client.go_to_position([xarm_positions.poses["TRANSPORT_STEP_1"], xarm_positions.poses["BOX_STEP_1"], xarm_positions.poses["BOX_2_STEP_2"]],angle_speed=speed)
                    if not robot_result.get('success', False):
                        logger.error(f"Robot movement failed: {robot_result.get('error')}")
                        return False
                    
                    return True
    except Exception as e:
        logger.error(f"Go to box 1 error: {e}")
        return e

async def changePosition(stop_event, position, speed = default_speed):
    try:
        if "SECTION" in position:
            async with xarm_client as client:
                robot_result = await client.go_to_position([xarm_positions.poses["READY_STEP_1"],xarm_positions.poses["READY_STEP_2"],xarm_positions.poses[position]],angle_speed=speed)
                if not robot_result.get('success', False):
                    logger.error(f"Robot movement failed: {robot_result.get('error')}")
    except Exception as e:
        logger.error(f"Change position error: {e}")