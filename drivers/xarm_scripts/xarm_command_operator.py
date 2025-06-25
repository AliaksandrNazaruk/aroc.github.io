from xarm.wrapper import XArmAPI
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + "/../.."))

from drivers.xarm_scripts import (
    get_robot_data,
    take,
    put,
    move_to_position,
    get_position,
    move_tool_position,
    move_to_pose,
)
from core.configuration import xarm_manipulator_ip
import logging
import asyncio

logger = logging.getLogger(__name__)
locker = False

async def xarm_command_operator(data):
    global locker
    if locker:
        raise RuntimeError(f"Failed to connect to manipulator: xArm is busy")
    arm = None
    robot_main = None
    try:
        try:
            locker = True
            arm = XArmAPI(xarm_manipulator_ip, baud_checkset=False)
        except asyncio.TimeoutError:
            raise RuntimeError(f"Failed to connect to manipulator: Timeout")
        
        arm.get_robot_sn()
        if not arm.connected:
            raise RuntimeError(f"Failed to connect to manipulator: xArm is not ready to connect")
            
        if data["command"] == "move_to_position":
            robot_main = move_to_position.RobotMain(arm)
        elif data["command"] == "move_tool_position":
            robot_main = move_tool_position.RobotMain(arm)
        elif data["command"] == "move_to_pose":
            robot_main = move_to_pose.RobotMain(arm)
        elif data["command"] == "take":
            robot_main = take.RobotMain(arm)
        elif data["command"] == "put":
            robot_main = put.RobotMain(arm)
        elif data["command"] == "get_current_position":
            robot_main = get_position.RobotMain(arm)
        elif data["command"] == "get_data":
            robot_main = get_robot_data.RobotMain(arm)
        else:
            raise RuntimeError(f"{data['command']} command not found")
        
        result = robot_main.run(data)
        return {
            "success": True,
            "result": result,
            "error": None,
            "error_code": 0
        }
        
    except Exception as e:
        raise RuntimeError(f"XARM Operator error: {type(e).__name__}: {e}")
    finally:
        locker = False
        if arm is not None:
            arm.disconnect()

# data= {}
# data["command"] = "move_to_pose"
# data["pose_name"] = "READY_SECTION_CENTER"

# result = xarm_command_operator(data)
# #