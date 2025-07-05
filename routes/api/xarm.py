from fastapi import APIRouter
from typing import Union, Dict, Optional
from application.xarm_scripts import *
from core.state import task_manager
from models.api_types import (
    XarmMoveWithJointsDictParams, XarmMoveWithJointsParams, XarmMoveWithPoseParams,
    XarmMoveWithToolParams, XarmCommandResponse, XarmAsyncResponse,
    XarmStatusResponse, XarmJointsPositionResponse, TaskStatusResponse,ErrorStatus
)
from utils.api import endpoint_guard, endpoint_with_lock_guard

router = APIRouter(prefix="/api/v1/xarm", tags=["xArm Manipulator"])

@router.get(
    "/manipulator/task_status/{task_id}",
    response_model=TaskStatusResponse,
)
async def get_manipulator_task_status(task_id: str):
    status = task_manager.get_status(task_id)
    return status

@router.post(
    "/manipulator/complex_move/with_joints_dict",
    response_model=Union[XarmCommandResponse, XarmAsyncResponse],
)
@endpoint_with_lock_guard(manipulator_lock)
async def complex_move_with_joints_dict(params: XarmMoveWithJointsDictParams):
    if params.blocking:
        result = await complex_move_with_joints(params)
        return XarmCommandResponse(success=result)
    else:
        return await wrap_async_task(
            lambda: complex_move_with_joints(params),
            XarmAsyncResponse
        )

@router.post(
    "/manipulator/move/change_joints",
    response_model=Union[XarmCommandResponse, XarmAsyncResponse],
)
@endpoint_with_lock_guard(manipulator_lock)
async def change_joints(params: XarmMoveWithJointsParams):
    if params.blocking:
        result = await move_with_joints(params)
        return XarmCommandResponse(success=result)
    else:
        return await wrap_async_task(
            lambda: move_with_joints(params),
            XarmAsyncResponse
        )

@router.post(
    "/manipulator/move/change_pose",
    response_model=Union[XarmCommandResponse, XarmAsyncResponse],
)
@endpoint_with_lock_guard(manipulator_lock)
async def change_pose(params: XarmMoveWithPoseParams):
    if params.blocking:
        result = await move_to_pose(params)
        return XarmCommandResponse(success=result)
    else:
        return await wrap_async_task(
            lambda: move_to_pose(params),
            XarmAsyncResponse
        )

@router.post(
    "/manipulator/move/change_tool_position",
    response_model=Union[XarmCommandResponse, XarmAsyncResponse],
)
@endpoint_with_lock_guard(manipulator_lock)
async def change_tool_position(params: XarmMoveWithToolParams):
    if params.blocking:
        result = await move_tool_position(params)
        return XarmCommandResponse(success=result)
    else:
        return await wrap_async_task(
            lambda: move_tool_position(params),
            XarmAsyncResponse
        )

@router.post(
    "/manipulator/drop",
    response_model=XarmCommandResponse,
)
@endpoint_guard()
async def api_gripper_drop():
    result = gripper_drop()
    return XarmCommandResponse(success=result)

@router.post(
    "/manipulator/take",
    response_model=XarmCommandResponse,
)
@endpoint_guard()
async def api_gripper_take():
    result = gripper_take()
    return XarmCommandResponse(success=result)

@router.get(
    "/manipulator/fault_reset",
    response_model=XarmStatusResponse,
)
@endpoint_with_lock_guard(manipulator_lock, XarmStatusResponse)
async def api_reset_faults():
    return reset_faults()

# @router.get(
#     "/manipulator/status",
#     response_model=Union[XarmStatusResponse, ErrorStatus],
# )
# @endpoint_guard(Union[XarmStatusResponse, ErrorStatus])
# async def api_get_manipulator_status():
#     try:
#         data = get_manipulator_status()
#         return XarmStatusResponse(**data)
#     except Exception as e:
#         error = {"type": type(e.args[0]).__name__, "msg": e.args[0]._message}
#         return ErrorStatus(error=error)

@router.get(
    "/manipulator/current_position",
    response_model=Optional[dict],
)
@endpoint_guard()
async def api_get_current_position():
    result = get_current_position()
    return {"pose_name": result[0], "points": result[1]}

@router.get(
    "/manipulator/joints_position",
    response_model=XarmJointsPositionResponse,
)
@endpoint_guard(XarmJointsPositionResponse)
async def api_get_manipulator_joints_position():
    result = get_joints_position()
    return {"joints": result[1]}

@router.post("/joystick")
@endpoint_guard(manipulator_lock)
async def api_joystick_control(stream_data: Dict):
    result = joystick_control(stream_data)
    return result
