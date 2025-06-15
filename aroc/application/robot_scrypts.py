import asyncio
import time
from typing import Any, Dict

from core.state import xarm_client, igus_client
from fastapi import HTTPException
import traceback

import drivers.xarm_scripts.xarm_positions as xarm_positions
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


async def check_devices_ready() -> bool:
    """Ensure XArm, Igus and AGV are operational before running a script."""

    xarm_state: Dict[str, Any] = {}
    igus_state: Dict[str, Any] = {}
    # agv_state = {"online": symovo_car.online}

    async def fetch_xarm_state() -> Dict[str, Any]:
        async with xarm_client as client:
            state = await client.get_data()
            if (
                state.get("has_err_warn")
                or state.get("has_error")
                or state.get("has_warn")
            ):
                raise RuntimeError("xarm has warnings or errors")
            return state

    async def fetch_igus_state() -> Dict[str, Any]:
        async with igus_client as client:
            state = await client.get_state()
            if not state.get("homing", False):
                raise RuntimeError("igus not homed")
            if state.get("error"):
                raise RuntimeError("igus reports error")
            return state

    results = await asyncio.gather(
        fetch_xarm_state(), fetch_igus_state(), return_exceptions=True
    )

    def exc_details(e):
        return {
            "type": type(e).__name__,
            "msg": str(e.args[0]),
        }

    if isinstance(results[0], Exception):
        logger.error("Failed to fetch XArm state: %s", results[0])
        xarm_state = {"error": exc_details(results[0])}
    else:
        xarm_state = results[0]

    if isinstance(results[1], Exception):
        logger.error("Failed to fetch Igus state: %s", results[1])
        igus_state = {"error": exc_details(results[1])}
    else:
        igus_state = results[1]

    xarm_ready = (
        xarm_state.get("connected")
        and not xarm_state.get("has_error")
        and not xarm_state.get("has_err_warn")
        and xarm_state.get("error_code", 0) == 0
    )
    igus_ready = (
        igus_state.get("connected")
        and igus_state.get("homing")
        and not igus_state.get("error")
    )
    # agv_ready = agv_state["online"]

    # if not (xarm_ready and igus_ready and agv_ready):
    if not (xarm_ready and igus_ready):
        detail = {
            "xarm": xarm_state,
            "igus": igus_state,
            # "symovo": agv_state,
        }
        # Compose a short human readable message so that the frontend can
        # display a clear error instead of "[object Object]".
        missing = []
        if not xarm_ready:
            missing.append("XArm")
        if not igus_ready:
            missing.append("Igus")
        # if not agv_ready:
        #     missing.append("AGV")
        message = "{} not ready".format(", ".join(missing)) if missing else "Devices not ready"

        raise HTTPException(
            status_code=400,
            detail={"message": message, "states": detail},
        )
    return True

async def script_operator(stop_event, data):
    """
    Execute robot script based on command.
    
    Args:
        stop_event: Event to signal script termination
        command: Command to execute
    """
    command = data['command']
    await check_devices_ready()
    try:
        if command == "box_1":
            return await goToBox1(stop_event)
        elif command == "box_2":
            return await goToBox2(stop_event)
        elif command == "transport":
            return await transport_position(stop_event)
        elif "change_position" == command:
            return await changePosition(stop_event, data['position_name'], speed=int(data['speed']))

    except Exception as e:
        logger.error(f"Script operator error: {e}")
        raise


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
    """Move robot to Box 1 position."""
    first_pos = 40000
    second_pos = 30000
    try:
        async with igus_client as _igus_client:
            igus_result = await _igus_client.move_to_position(first_pos, (speed * 100), (speed * 100), True)
            if not igus_result.get("success", False):
                error_msg = igus_result.get("error", "Igus move failed")
                logger.error(f"Igus movement failed: {error_msg}")
                raise Exception(error_msg)

            igus_position = await igus_client.get_position()
            igus_position = igus_position.get('position')
            result = abs(igus_position - first_pos)
            if result < 250:
                async with xarm_client as _xarm_client:
                    current_pose = await _xarm_client.get_current_position()
                    igus_result = await _igus_client.move_to_position(int(second_pos), int((speed * 100)/3), int((speed * 100)/2), False)

                    if not igus_result.get('success', False):
                        error_msg = igus_result.get('error', 'Igus move failed')
                        logger.error(f"Igus movement failed: {error_msg}")
                        raise Exception(error_msg)

                    robot_result = await _xarm_client.go_to_position([xarm_positions.poses["TRANSPORT_STEP_1"], xarm_positions.poses["BOX_STEP_1"], xarm_positions.poses["BOX_1_STEP_2"]], angle_speed=speed)

                    if not robot_result:
                        error_msg = robot_result.get('error', 'Robot move failed')
                        logger.error(f"Robot movement failed: {error_msg}")
                        raise Exception(error_msg)

                    return True

            raise Exception("Position tolerance exceeded")

    except Exception as e:
        logger.error(f"Go to box 1 error: {e}")
        raise

async def goToBox2(stop_event, speed = default_speed):
    """Move robot to Box 2 position."""
    first_pos = 40000
    second_pos = 30000
    try:
        async with igus_client as _igus_client:
            igus_result = await _igus_client.move_to_position(first_pos, (speed * 100), (speed * 100), True)
            if not igus_result.get("success", False):
                error_msg = igus_result.get("error", "Igus move failed")
                logger.error(f"Igus movement failed: {error_msg}")
                raise Exception(error_msg)

            igus_position = await igus_client.get_position()
            igus_position = igus_position.get('position')
            result = abs(igus_position - first_pos)
            if result < 250:
                async with xarm_client as _xarm_client:
                    current_pose = await _xarm_client.get_current_position()
                    igus_result = await _igus_client.move_to_position(int(second_pos), int((speed * 100)/3), int((speed * 100)/2), False)

                    if not igus_result.get('success', False):
                        error_msg = igus_result.get('error', 'Igus move failed')
                        logger.error(f"Igus movement failed: {error_msg}")
                        raise Exception(error_msg)

                    robot_result = await _xarm_client.go_to_position([xarm_positions.poses["TRANSPORT_STEP_1"], xarm_positions.poses["BOX_STEP_1"], xarm_positions.poses["BOX_2_STEP_2"]], angle_speed=speed)

                    if not robot_result:
                        error_msg = robot_result.get('error', 'Robot move failed')
                        logger.error(f"Robot movement failed: {error_msg}")
                        raise Exception(error_msg)

                    return True

            raise Exception("Position tolerance exceeded")

    except Exception as e:
        logger.error(f"Go to box 2 error: {e}")
        raise

async def changePosition(stop_event, position, speed = default_speed):
    try:
        if "SECTION" in position:
            async with xarm_client as client:
                robot_result = await client.go_to_position([xarm_positions.poses["READY_STEP_1"],xarm_positions.poses["READY_STEP_2"],xarm_positions.poses[position]],angle_speed=speed)
                if not robot_result.get('success', False):
                    logger.error(f"Robot movement failed: {robot_result.get('error')}")
    except Exception as e:
        logger.error(f"Change position error: {e}")