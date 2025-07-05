from fastapi import APIRouter, HTTPException
from core.state import xarm_client, igus_client, symovo_client
from core.logger import server_logger
from models.api_types import DefaultMoveRequest,RobotMoveRequest,RobotTransportPositionResult,RobotMoveResult,RobotMoveBoxResult,RobotSystemStatus
from application.robot_scripts import *
import drivers.xarm_driver.xarm_positions as xarm_positions

router = APIRouter(prefix="/api/v1/robot", tags=["Robot AE.01"])

@router.post(
    "/move/to_product",
    response_model=RobotMoveResult,
    summary="Move robot to product location",
    description="""
Moves the robot to the specified product location, using all subsystems (AGV, lift, manipulator).  
All movements are coordinated. If any subsystem fails, execution halts and an error is returned.

**Parameters:**
- `product_id`: Identifier of the product to handle.
- `location`: Target location on the AGV map.
- `lift_position`: Optional. Desired Igus lift position (int).
- `manipulator_offsets`: Optional. Tool offsets for xArm manipulator.
- `velocity`: Movement speed in percent (1-100).
- `reset_faults`: If true, resets errors and reinitializes before movement.
- `blocking`: If true, waits until movement completes before returning.

**Typical workflow:**  
1. Move AGV to target location  
2. Raise/lower lift  
3. Move manipulator to specified offsets

If the robot is busy or a device fails, the call returns an error (status 423/500).

""",
    response_description="Result of coordinated movement",
    responses={
        200: {
            "description": "Movement executed successfully",
        },
        500: {
            "description": "Failed to move due to error in one of the subsystems",
        }
    }
)
async def move_to_product(params: RobotMoveRequest) -> RobotMoveResult:
    server_logger.log_event("info", f"POST /api/system/move_to_product {params}")
    result = await move_robot_to_product(
        symovo_client, igus_client, xarm_client, xarm_positions, params
    )
    if not result.get("success", False):
        server_logger.log_event("error", f"System move_to_product failed: {result.get('message', '')}")
        raise HTTPException(status_code=500, detail=result.get("message", "Unknown error"))
    server_logger.log_event("info", "System move_to_product executed successfully")
    return MoveResult(**result)

@router.post(
    "/move/to_box_1",
    response_model=RobotMoveBoxResult,
    summary="Move robot to Box 1",
    description="""
Moves the robot to the preconfigured Box 1 drop-off position.

**Steps:**
1. Moves Igus lift to intermediate position.
2. Moves xArm manipulator through preset waypoints to Box 1.
3. Moves Igus lift to final position for drop-off.

If any step fails, execution halts and an error is returned.

**Parameters:**
- `velocity`: Movement speed in percent (1-100).

""",
    response_description="Result of movement to Box 1",
    responses={
        200: {
            "description": "Product placed in Box 1 successfully.",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "igus_result": {
                            "success": True,
                            "position": 30,
                            "details": "Lift moved to position 30"
                        },
                        "manipulator_result": {
                            "success": True,
                            "details": "Manipulator executed drop-off sequence"
                        },
                        "message": ""
                    }
                }
            }
        },
        500: {
            "description": "Failed to move due to error in one of the subsystems.",
            "content": {
                "application/json": {
                    "example": {
                        "success": False,
                        "igus_result": {
                            "success": False,
                            "error": "Igus move failed"
                        },
                        "manipulator_result": None,
                        "message": "Igus move failed: Homing required"
                    }
                }
            }
        }
    }
)
async def move_to_box_1(params: DefaultMoveRequest) -> RobotMoveBoxResult:
    result = await move_robot_to_box_1(params.velocity_percent)
    return RobotMoveBoxResult(**result)

@router.post(
    "/move/to_box_2",
    response_model=RobotMoveBoxResult,
    summary="Move robot to Box 2",
    description="""
Moves the robot to the preconfigured Box 1 drop-off position.

**Steps:**
1. Moves Igus lift to intermediate position.
2. Moves xArm manipulator through preset waypoints to Box 2.
3. Moves Igus lift to final position for drop-off.

If any step fails, execution halts and an error is returned.

**Parameters:**
- `velocity`: Movement speed in percent (1-100).

""",
    response_description="Result of movement to Box 2",
    responses={
        200: {
            "description": "Product placed in Box 2 successfully.",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "igus_result": {
                            "success": True,
                            "position": 30,
                            "details": "Lift moved to position 30"
                        },
                        "manipulator_result": {
                            "success": True,
                            "details": "Manipulator executed drop-off sequence"
                        },
                        "message": ""
                    }
                }
            }
        },
        500: {
            "description": "Failed to move due to error in one of the subsystems.",
            "content": {
                "application/json": {
                    "example": {
                        "success": False,
                        "igus_result": {
                            "success": False,
                            "error": "Igus move failed"
                        },
                        "manipulator_result": None,
                        "message": "Igus move failed: Homing required"
                    }
                }
            }
        }
    }
)
async def move_to_box_2(params: DefaultMoveRequest) -> RobotMoveBoxResult:
    result = await move_robot_to_box_2(params.velocity_percent)
    return RobotMoveBoxResult(**result)

@router.post(
    "/move/to_transport_position",
    response_model=RobotTransportPositionResult,
    summary="Move robot to transport position",
    description="""
Moves the robot into its transport (stowed) position.

**Sequence:**
1. Moves Igus lift to intermediate (safe) height.
2. (If needed) Moves xArm manipulator through transport waypoints.
3. Moves Igus lift to its base (zero) position.

If any subsystem fails, the operation halts and an error is returned.

**Parameters:**
- `velocity`: Movement speed in percent (1-100).

""",
    response_description="Result of moving to transport position",
    responses={
        200: {
            "description": "Transport position reached successfully.",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "igus_result": {
                            "success": True,
                            "position": 20,
                            "details": "Lift moved to intermediate position"
                        },
                        "manipulator_result": {
                            "success": True,
                            "details": "Manipulator moved to transport waypoints"
                        },
                        "igus_final_result": {
                            "success": True,
                            "position": 0,
                            "details": "Lift moved to base position"
                        },
                        "message": ""
                    }
                }
            }
        },
        500: {
            "description": "Failed to move due to error in one of the subsystems.",
            "content": {
                "application/json": {
                    "example": {
                        "success": False,
                        "igus_result": {
                            "success": False,
                            "error": "Igus move failed"
                        },
                        "manipulator_result": None,
                        "igus_final_result": None,
                        "message": "Igus move failed: Homing required"
                    }
                }
            }
        }
    }
)
async def transport_position(params: DefaultMoveRequest) -> RobotTransportPositionResult:
    result = await move_to_transport_position(
        igus_client, xarm_client, xarm_positions, params.velocity
    )
    return TransportPositionResult(**result)

@router.get(
    "/status",
    response_model=RobotSystemStatus,
    summary="Get robot system status",
    description="Returns full status of all robot subsystems. Response is always a flat structure with 'ready' and 'message' in root.",
    response_description="Full status of the robot cell."
)
async def check_devices_ready() -> RobotSystemStatus:
    result = await get_robot_system_status()
    return RobotSystemStatus(**result)
