# xarm_backend.py

import asyncio
from typing import Callable, Dict
from core.state import xarm_manager

manipulator_lock = asyncio.Lock()

async def guarded_manipulator_command(func: Callable, *args, **kwargs):
    if manipulator_lock.locked():
        raise RuntimeError("Manipulator_lock is busy")
    async with manipulator_lock:
        return await _execute_manipulator_command(func, *args, **kwargs)

async def _execute_manipulator_command(func: Callable, *args, **kwargs):
    loop = asyncio.get_event_loop()
    try:
        result = await loop.run_in_executor(None, lambda: func(*args, **kwargs))
        if hasattr(result, "result") and hasattr(result, "done"):
            result = result.result(timeout=10)
        return result
    except Exception as e:
        raise RuntimeError(f"{func.__name__} failed: {e}")

async def complex_move_with_joints(params):
    robot_main = xarm_manager.get_instance(reset=params.reset_faults)
    return await guarded_manipulator_command(robot_main.complex_move_with_joints, params)

async def move_with_joints(params):
    robot_main = xarm_manager.get_instance(reset=params.reset_faults)
    return await guarded_manipulator_command(robot_main.move_with_joints, params)

async def move_to_pose(params):
    robot_main = xarm_manager.get_instance(reset=params.reset_faults)
    return await guarded_manipulator_command(robot_main.move_to_pose, params)

async def move_tool_position(params):
    robot_main = xarm_manager.get_instance(reset=params.reset_faults)
    return await guarded_manipulator_command(robot_main.move_tool_position, params)

def gripper_drop():
    robot_main = xarm_manager.get_instance()
    return robot_main.drop()

def gripper_take():
    robot_main = xarm_manager.get_instance()
    return robot_main.take()

def reset_faults():
    xarm_manager._create_new_instance()
    robot_main = xarm_manager.get_instance()
    return robot_main.get_status()

def get_manipulator_status():
    robot_main = xarm_manager.get_instance()
    return robot_main.get_status()

def get_current_position():
    robot_main = xarm_manager.get_instance()
    return robot_main.get_current_position()

def get_joints_position():
    robot_main = xarm_manager.get_instance()
    return robot_main.get_joints_position()

def joystick_control(stream_data: Dict):
    robot_main = xarm_manager.get_instance()
    return robot_main.handle_joystick_stream(stream_data)
