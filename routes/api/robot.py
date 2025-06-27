from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
import asyncio

from core.state import xarm_client, igus_client, symovo_car
from core.logger import server_logger
import drivers.xarm_scripts.xarm_positions as xarm_positions

router = APIRouter(prefix="/api/v1/robot", tags=["Robot AE.01"])

class ProductLocation(BaseModel):
    """Coordinates of a product on the AGV map."""

    x: float = Field(
        ...,
        description="X position in millimetres",
        json_schema_extra={"example": 0.0},
    )
    y: float = Field(
        ...,
        description="Y position in millimetres",
        json_schema_extra={"example": 0.0},
    )
    theta: float = Field(
        0.0,
        description="Orientation angle in radians",
        json_schema_extra={"example": 0.0},
    )
    map_id: Optional[str] = Field(
        None,
        description="Map identifier used by the AGV",
        json_schema_extra={"example": "factory_map"},
    )


class XarmMoveWithToolOffsets(BaseModel):
    x_offset: float = Field(
        ...,
        ge=-1000.0, le=1000.0,
        description="X offset for Tool in mm (-1000..1000.0)",
        json_schema_extra={"example": 0}
    )
    y_offset: float = Field(
        ...,
        ge=-1000.0, le=1000.0,
        description="Y offset for Tool in mm (-1000..1000.0)",
        json_schema_extra={"example": 0}
    )
    z_offset: float = Field(
        ...,
        ge=-1000.0, le=1000.0,
        description="Z offset for Tool in mm (-1000..1000.0)",
        json_schema_extra={"example": 0}
    )

class DefaultMoveRequest(BaseModel):
    velocity: float = Field(
        ...,
        ge=1, le=100.0,
        description="Robot speed in percents (0..100.0)",
        json_schema_extra={"example": 20}
    )

class RobotStatusRequest(BaseModel):
    alive: bool = Field(
        ...,
        description="Service process responding",
        json_schema_extra={"example": True},
    )
    connected: bool = Field(
        ...,
        description="Robot controller connection state",
        json_schema_extra={"example": False},
    )
    state: int = Field(
        ...,
        description="Current raw state code reported by the robot",
        json_schema_extra={"example": 0},
    )
    has_err_warn: bool = Field(
        ...,
        description="True if the robot has warnings or errors",
        json_schema_extra={"example": True},
    )
    has_error: bool = Field(
        ...,
        description="True if a fatal error is present",
        json_schema_extra={"example": False},
    )
    has_warn: bool = Field(
        ...,
        description="True if warnings are present",
        json_schema_extra={"example": True},
    )
    error_code: int = Field(
        ...,
        description="Numeric error code, 0 if no error",
        json_schema_extra={"example": 0},
    )

class RobotMoveRequest(BaseModel):
    product_id: str = Field(
        ...,
        description="Identifier of the product to handle",
        json_schema_extra={"example": "PRODUCT_1"},
    )
    location: ProductLocation = Field(
        ...,
        description="Target location of the product",
    )
    lift_position: Optional[int] = Field(
        None,
        description="Lift position for the Igus motor",
        json_schema_extra={"example": 30000},
    )
    manipulator_coords: Optional[XarmMoveWithToolOffsets] = Field(
        None,
        description="Tool offsets for the xArm manipulator",
    )
    velocity: float = Field(
        ...,
        ge=1, le=100.0,
        description="Robot speed in percents (0..100.0)",
        json_schema_extra={"example": 20}
    )
    reset_faults: bool = Field(
        False,
        description="Resetting errors and reinitializing the robot before movement, the task execution will last 3-5 seconds longer)",
        json_schema_extra={"example": False}
    )
    blocking: bool = Field(
        True,
        description="Wait until move is complete (true: wait for completion before returning response, false: return immediately)",
        json_schema_extra={"example": True}
    )

@router.post("/move/to_product", response_model=Dict[str, Any])
async def move_to_product(params: RobotMoveRequest):
    """Move a product to the specified location using all subsystems."""
    server_logger.log_event("info", f"POST /api/system/move_to_product {params}")

    # Безопасно устанавливаем скорость
    speed = params.velocity or 20
    igus_result = None
    robot_result = None
    agv_result = None

    try:
        # 1. Подъемник (лифт)
        if params.lift_position is not None:
            async with igus_client as _igus_client:
                igus_result = await _igus_client.move_to_position(
                    int(params.lift_position), speed, speed, params.blocking
                )
                if not igus_result.get("success", False):
                    error_msg = igus_result.get("error", "Igus move failed")
                    server_logger.log_event("error", f"Igus movement failed: {igus_result}")
                    raise Exception(error_msg)

        # 2. Манипулятор
        if params.manipulator_coords:
            async with xarm_client as client:
                await changePosition(
                    client,
                    position=xarm_positions.poses["READY_SECTION_CENTER"],
                    speed=speed,
                    wait=True
                )
                robot_result = await client.move_tool_position(
                    params.manipulator_coords.x_offset ,
                    params.manipulator_coords.y_offset ,
                    params.manipulator_coords.z_offset ,
                    velocity=speed,
                    blocking=params.blocking
                )
                if not robot_result.get('success', False):
                    server_logger.log_event("error", f"Manipulator move failed: {robot_result}")
                    raise Exception("Robot movement failed")

        # 3. AGV (коммент не удаляй, если потом потребуется добавить)
        # agv_result = ...

    except Exception as e:
        server_logger.log_event("error", f"System move_to_product failed: {e}")
        raise HTTPException(status_code=500, detail=f"detail: {e}")

    server_logger.log_event("info", "System move_to_product executed successfully")
    return {
        "success": True,
        "agv_result": agv_result,
        "lift_result": igus_result,
        "manipulator_result": robot_result,
    }

@router.post("/move/to_box_1", response_model=Dict[str, Any])
async def move_to_box_1(params: DefaultMoveRequest):
    """Move the robot to the preconfigured Box 1 drop-off position."""
    first_pos = 40000
    second_pos = 30000
    try:
        async with igus_client as _igus_client:
            igus_result = await _igus_client.move_to_position(first_pos, params.velocity, params.velocity, True)
            if not igus_result.get("success", False):
                error_msg = igus_result.get("error", "Igus move failed")
                raise Exception(error_msg)

            igus_position = await igus_client.get_status()
            igus_position = igus_position.get('position')
            result = abs(igus_position - first_pos)
            if result < 250:
                async with xarm_client as _xarm_client:
                    current_pose = await _xarm_client.get_current_position()
                    igus_result = await _igus_client.move_to_position(int(second_pos), int(params.velocity/2), int(params.velocity/2), False)
                    if not igus_result.get('success', False):
                        error_msg = igus_result.get('error', 'Igus move failed')
                        raise Exception(error_msg)

                    robot_result = await _xarm_client.complex_move_with_joints_dict(
                        points=[xarm_positions.poses["TRANSPORT_STEP_1"], xarm_positions.poses["BOX_STEP_1"], xarm_positions.poses["BOX_1_STEP_2"]],
                        velocity=params.velocity,
                        blocking=True,
                        reset_faults=False
                    )
                    if not robot_result:
                        error_msg = robot_result.get('error', 'Robot move failed')
                        raise Exception(error_msg)
                    return robot_result
            raise Exception("Position tolerance exceeded")
    except Exception as e:
        raise

@router.post("/move/to_box_2", response_model=Dict[str, Any])
async def move_to_box_2(params: DefaultMoveRequest):
    """Move the robot to the Box 2 drop-off position."""
    first_pos = 40000
    second_pos = 30000
    try:
        async with igus_client as _igus_client:
            igus_result = await _igus_client.move_to_position(first_pos, params.velocity, params.velocity, True)
            if not igus_result.get("success", False):
                error_msg = igus_result.get("error", "Igus move failed")
                raise Exception(error_msg)

            igus_position = await igus_client.get_status()
            igus_position = igus_position.get('position')
            result = abs(igus_position - first_pos)
            if result < 250:
                async with xarm_client as _xarm_client:
                    current_pose = await _xarm_client.get_current_position()
                    igus_result = await _igus_client.move_to_position(int(second_pos), int(params.velocity/2), int(params.velocity/2), False)
                    if not igus_result.get('success', False):
                        error_msg = igus_result.get('error', 'Igus move failed')
                        raise Exception(error_msg)

                    robot_result = await _xarm_client.complex_move_with_joints_dict(
                        points=[xarm_positions.poses["TRANSPORT_STEP_1"], xarm_positions.poses["BOX_STEP_1"], xarm_positions.poses["BOX_2_STEP_2"]],
                        velocity=params.velocity,
                        blocking=True,
                        reset_faults=False
                    )
                    if not robot_result:
                        error_msg = robot_result.get('error', 'Robot move failed')
                        raise Exception(error_msg)
                    return robot_result
            raise Exception("Position tolerance exceeded")
    except Exception as e:
        raise

@router.post("/move/to_transport_position", response_model=Dict[str, Any])
async def transport_position(params: DefaultMoveRequest):
    """Move the robot into its transport (stowed) position."""
    try:
        async with igus_client as _igus_client:
            igus_result = await _igus_client.move_to_position(20000,params.velocity,params.velocity,True)
            if not igus_result.get("success", False):
                error_msg = igus_result.get("error", "Igus move failed")
                raise Exception(error_msg)
            async with xarm_client as client:
                current_pose = await client.get_current_position()
                if current_pose['pose_name'] != "TRANSPORT_STEP_2":
                    robot_result = await client.complex_move_with_joints_dict(
                        points=[xarm_positions.poses["TRANSPORT_STEP_1"], xarm_positions.poses["TRANSPORT_STEP_2"]],
                        velocity=params.velocity,
                        blocking=True,
                        reset_faults=False
                    )
                    if not robot_result:
                        error_msg = robot_result.get('error', 'Robot move failed')
                        raise Exception(error_msg)
                igus_result2 = await _igus_client.move_to_position(0,params.velocity,params.velocity,True)
                if not igus_result2.get("success", False):
                    error_msg = igus_result.get("error", "Igus move failed")
                    raise Exception(error_msg)
        raise Exception("Transport position failed")
    except Exception as e:
        return False

async def changePosition(client, position, speed, wait=True, reset_faults=False):
    """Move the xArm through ready poses to a target position."""
    try:
        robot_result = await client.complex_move_with_joints_dict(
            points=[xarm_positions.poses["READY_STEP_1"], xarm_positions.poses["READY_STEP_2"], position],
            velocity=speed,
            blocking=wait,
            reset_faults=reset_faults
        )
        if not robot_result.get('success', False):
            raise Exception(f"Robot movement failed: {robot_result}")
        return True
    except Exception as e:
        raise Exception("Robot movement failed")
    
@router.get(
    "/status",
    response_model=RobotStatusRequest,
    summary="Get robot status",
    description="""
        Returns the current status of the robot.<br>
        If the robot is busy executing another command, returns HTTP 423 Locked.
        """,
    response_description="Current status of the robot.",
    responses={
        200: {"description": "Status retrieved"},
        423: {"description": "robot is busy"},
        503: {"description": "Error retrieving robot status"},
    }
)
async def check_devices_ready() -> bool:
    """Return ``True`` if the xArm, Igus lift and AGV are all operational."""

    xarm_state: Dict[str, Any] = {}
    igus_state: Dict[str, Any] = {}
    agv_state = {"online": symovo_car.online}

    async def fetch_xarm_state() -> Dict[str, Any]:
        async with xarm_client as client:
            state = await client.get_status()
            if (
                state.get("has_err_warn")
                or state.get("has_error")
                or state.get("has_warn")
            ):
                raise RuntimeError("xarm has warnings or errors")
            return state

    async def fetch_igus_state() -> Dict[str, Any]:
        async with igus_client as client:
            state = await client.get_status()
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
        xarm_state = {"error": exc_details(results[0])}
    else:
        xarm_state = results[0]

    if isinstance(results[1], Exception):
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
    agv_ready = agv_state["online"]

    if not (xarm_ready and igus_ready and agv_ready):
    # if not (xarm_ready and igus_ready):
        detail = {
            "xarm": xarm_state,
            "igus": igus_state,
            "symovo": agv_state,
        }
        # Compose a short human readable message so that the frontend can
        # display a clear error instead of "[object Object]".
        missing = []
        if not xarm_ready:
            missing.append("XArm")
        if not igus_ready:
            missing.append("Igus")
        if not agv_ready:
            missing.append("AGV")
        message = "{} not ready".format(", ".join(missing)) if missing else "Devices not ready"

        raise HTTPException(
            status_code=400,
            detail={"message": message, "states": detail},
        )
    return True