import asyncio
import drivers.xarm_driver.xarm_positions as xarm_positions
from core.state import igus_client, xarm_client, symovo_client
from models.api_types import IgusMoveParams,XarmStatusResponse,IgusStatusResponse,SymovoStatusResponse,ErrorStatus
import logging

logger = logging.getLogger(__name__)

async def move_robot_to_box_1(velocity: int) -> dict:
    first_pos = 40
    second_pos = 30
    try:
        async with igus_client as _igus_client:
            param = {"position_cm":first_pos,
                     "velocity_percent":velocity,
                     "acceleration_percent":velocity,
                     "blocking":True,
                     }
            igus_result = await _igus_client.move_to_position(param)
            if not igus_result.get("success", False):
                return {
                    "success": False,
                    "igus_result": igus_result,
                    "message": igus_result.get("error", "Igus move failed")
                }

            igus_position = await igus_client.get_status()
            igus_position = igus_position.get('position')
            result = abs(igus_position - first_pos)
            if result < 250:
                async with xarm_client as _xarm_client:
                    current_pose = await _xarm_client.get_current_position()
                    igus_result2 = await _igus_client.move_to_position(
                        int(second_pos), int(velocity / 2), int(velocity / 2), False
                    )
                    if not igus_result2.get('success', False):
                        return {
                            "success": False,
                            "igus_result": igus_result2,
                            "message": igus_result2.get('error', 'Igus move failed')
                        }
                    robot_result = await _xarm_client.complex_move_with_joints_dict(
                        points=[
                            xarm_positions.poses["TRANSPORT_STEP_1"],
                            xarm_positions.poses["BOX_STEP_1"],
                            xarm_positions.poses["BOX_1_STEP_2"]
                        ],
                        velocity=velocity,
                        blocking=True,
                        reset_faults=False
                    )
                    if not robot_result:
                        return {
                            "success": False,
                            "igus_result": igus_result2,
                            "manipulator_result": robot_result,
                            "message": robot_result.get('error', 'Robot move failed') if robot_result else "Robot move failed"
                        }
                    return {
                        "success": True,
                        "igus_result": igus_result2,
                        "manipulator_result": robot_result,
                        "message": ""
                    }
            return {
                "success": False,
                "igus_result": igus_result,
                "message": "Position tolerance exceeded"
            }
    except Exception as e:
        return {
            "success": False,
            "message": str(e)
        }

async def move_robot_to_box_2(velocity: int) -> dict:
    first_pos = 40
    second_pos = 30
    try:
        async with igus_client as _igus_client:
            igus_result = await _igus_client.move_to_position(first_pos, velocity, velocity, True)
            if not igus_result.get("success", False):
                return {
                    "success": False,
                    "igus_result": igus_result,
                    "message": igus_result.get("error", "Igus move failed")
                }

            igus_position = await igus_client.get_status()
            igus_position = igus_position.get('position')
            result = abs(igus_position - first_pos)
            if result < 250:
                async with xarm_client as _xarm_client:
                    current_pose = await _xarm_client.get_current_position()
                    igus_result2 = await _igus_client.move_to_position(
                        int(second_pos), int(velocity / 2), int(velocity / 2), False
                    )
                    if not igus_result2.get('success', False):
                        return {
                            "success": False,
                            "igus_result": igus_result2,
                            "message": igus_result2.get('error', 'Igus move failed')
                        }
                    robot_result = await _xarm_client.complex_move_with_joints_dict(
                        points=[
                            xarm_positions.poses["TRANSPORT_STEP_1"],
                            xarm_positions.poses["BOX_STEP_1"],
                            xarm_positions.poses["BOX_2_STEP_2"]
                        ],
                        velocity=velocity,
                        blocking=True,
                        reset_faults=False
                    )
                    if not robot_result:
                        return {
                            "success": False,
                            "igus_result": igus_result2,
                            "manipulator_result": robot_result,
                            "message": robot_result.get('error', 'Robot move failed') if robot_result else "Robot move failed"
                        }
                    return {
                        "success": True,
                        "igus_result": igus_result2,
                        "manipulator_result": robot_result,
                        "message": ""
                    }
            return {
                "success": False,
                "igus_result": igus_result,
                "message": "Position tolerance exceeded"
            }
    except Exception as e:
        return {
            "success": False,
            "message": str(e)
        }
    
async def move_to_transport_position(velocity: int) -> dict:
    # Возвращает dict с результатом, бизнес-логика не знает ничего о FastAPI или TransportPositionResult!
    try:
        async with igus_client as _igus_client:
            igus_result = await _igus_client.move_to_position(20, velocity, velocity, True)
            if not igus_result.get("success", False):
                return {
                    "success": False,
                    "igus_result": igus_result,
                    "message": igus_result.get("error", "Igus move failed")
                }
            manipulator_result = None
            with xarm_client as client:
                current_pose = await client.get_current_position()
                if current_pose.get('pose_name') != "TRANSPORT_STEP_2":
                    manipulator_result = await client.complex_move_with_joints_dict(
                        points=[xarm_positions.poses["TRANSPORT_STEP_1"], xarm_positions.poses["TRANSPORT_STEP_2"]],
                        velocity=velocity,
                        blocking=True,
                        reset_faults=False
                    )
                    if not manipulator_result or not manipulator_result.get('success', True):
                        return {
                            "success": False,
                            "igus_result": igus_result,
                            "manipulator_result": manipulator_result,
                            "message": manipulator_result.get('error', 'Robot move failed') if manipulator_result else 'Manipulator move failed'
                        }
            igus_result2 = await _igus_client.move_to_position(0, velocity, velocity, True)
            if not igus_result2.get("success", False):
                return {
                    "success": False,
                    "igus_result": igus_result,
                    "manipulator_result": manipulator_result,
                    "igus_final_result": igus_result2,
                    "message": igus_result2.get("error", "Igus move failed")
                }
            return {
                "success": True,
                "igus_result": igus_result,
                "manipulator_result": manipulator_result,
                "igus_final_result": igus_result2,
                "message": ""
            }
    except Exception as e:
        return {"success": False, "message": f"Transport position failed: {e}"}

async def move_robot_to_product(params) -> dict:
    """
    Бизнес-логика координированного движения к продукту.
    Возвращает dict с ключами: success, agv_result, lift_result, manipulator_result.
    Не использует типы и объекты FastAPI!
    """
    speed = params.velocity or 20
    igus_result = None
    robot_result = None
    agv_result = None

    try:
        # 1. AGV (если координаты указаны)
        if params.location.x != 0 and params.location.y != 0 and params.location.theta != 0:
            agv_result = symovo_client.move_to(
                params.location.x,
                params.location.y,
                params.location.theta,
                params.location.map_id,
                speed,
                True
            )
        # 2. Лифт
        if params.lift_position is not None:
            async with igus_client as _igus_client:
                igus_result = await _igus_client.move_to_position(
                    int(params.lift_position), speed, speed, params.blocking
                )
                if not igus_result.get("success", False):
                    error_msg = igus_result.get("error", "Igus move failed")
                    return {
                        "success": False,
                        "agv_result": agv_result,
                        "lift_result": igus_result,
                        "message": error_msg
                    }
        # 3. Манипулятор
        if params.manipulator_offsets:
            async with xarm_client as client:
                await changePosition(
                    client,
                    position=xarm_positions.poses["READY_SECTION_CENTER"],
                    speed=speed,
                    wait=True
                )
                robot_result = await client.move_tool_position(
                    params.manipulator_offsets.x_offset,
                    params.manipulator_offsets.y_offset,
                    params.manipulator_offsets.z_offset,
                    velocity=speed,
                    blocking=params.blocking
                )
                if not robot_result.get('success', False):
                    return {
                        "success": False,
                        "agv_result": agv_result,
                        "lift_result": igus_result,
                        "manipulator_result": robot_result,
                        "message": "Robot movement failed"
                    }

        return {
            "success": True,
            "agv_result": agv_result,
            "lift_result": igus_result,
            "manipulator_result": robot_result,
            "message": ""
        }
    except Exception as e:
        return {
            "success": False,
            "agv_result": agv_result,
            "lift_result": igus_result,
            "manipulator_result": robot_result,
            "message": str(e)
        }
    
async def changePosition(params) -> dict:
    """Move the xArm through ready poses to a target position."""
    try:
        robot_result = await xarm_client.complex_move_with_joints_dict(
            points=[xarm_positions.poses["READY_STEP_1"], xarm_positions.poses["READY_STEP_2"], position],
            velocity=params.speed,
            blocking=params.wait,
            reset_faults=params.reset_faults
        )
        if not robot_result.get('success', False):
            raise Exception(f"Robot movement failed: {robot_result}")
        return True
    except Exception as e:
        raise Exception("Robot movement failed")

async def get_robot_system_status() -> dict:
    xarm_state = {}
    igus_state = {}
    agv_state = {"online": symovo_client.online}

    async def fetch_xarm_state():
        async with xarm_client as client:
            state = await client.get_status()
            return state

    async def fetch_igus_state():
        async with igus_client as client:
            state = await client.get_status()
            return state

    async def fetch_symovo_state():
        state = symovo_client.get_status()
        return state
        
    results = await asyncio.gather(
        fetch_xarm_state(), fetch_igus_state(),fetch_symovo_state(), return_exceptions=True
    )

    def exc_details(e):
        return {
            "type": type(e).__name__,
            "msg": str(e.args[0]),
        }

    symovo_ready = (
        isinstance(results[2], SymovoStatusResponse)
        and results[2].connected
        and not results[2].has_error
        and not results[2].has_err_warn
        and results[2].error_code == 0
    )
    xarm_ready = (
        isinstance(results[0], XarmStatusResponse)
        and results[0].connected
        and not results[0].has_error
        and not results[0].has_err_warn
        and results[0].error_code == 0
    )
    igus_ready = (
        isinstance(results[1], IgusStatusResponse)
        and results[1].connected
        and results[1].homed
        and not results[1].error
    )

    ready = xarm_ready and igus_ready and symovo_ready
    if not ready:
        missing = []
        if not xarm_ready:
            missing.append("XArm")
        if not igus_ready:
            missing.append("Igus")
        if not symovo_ready:
            missing.append("AGV")
        message = "{} not ready".format(", ".join(missing)) if missing else "Devices not ready"
    else:
        message = ""

    return {
        "ready": ready,
        "message": message,
        "xarm": results[0],
        "igus": results[1],
        "symovo": results[2]
    }
