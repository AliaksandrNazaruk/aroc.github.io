from fastapi import APIRouter
from typing import Union
from models.api_types import (
    IgusAsyncResponse, TaskStatusResponse, IgusMoveParams,
    IgusPositionResponse, IgusMotionResponse, IgusStatusResponse,
    IgusCommandResponse,ErrorStatus
)
from core.state import task_manager
from application.igus_scripts import *
from utils.api import endpoint_with_lock_guard, endpoint_guard

router = APIRouter(prefix="/api/v1/igus", tags=["Igus Motor"])

@router.get(
    "/motor/task_status/{task_id}",
    response_model=TaskStatusResponse,
    summary="Get async task status",
)
@endpoint_guard(TaskStatusResponse)
async def get_motor_task_status(task_id: str):
    return task_manager.get_status(task_id)

@router.post(
    "/motor/move",
    response_model=Union[IgusCommandResponse, IgusAsyncResponse],
    summary="Move motor",
)
@endpoint_with_lock_guard(motor_lock, Union[IgusCommandResponse, IgusAsyncResponse])
async def move_motor(params: IgusMoveParams):
    if params.blocking:
        response = await move_motor_command(params.position_cm,params.velocity_percent,params.acceleration_percent,params.blocking)
        return IgusCommandResponse(**{"success": response})
    else:
        async def async_move():
            return await move_motor_command(params.position_cm,params.velocity_percent,params.acceleration_percent,params.blocking)
        task_id = task_manager.create_task(async_move())
        return IgusAsyncResponse(success=True, task_id=task_id)

@router.post(
    "/motor/reference",
    response_model=Union[IgusCommandResponse, IgusAsyncResponse],
    summary="Home (reference) motor",
)
@endpoint_with_lock_guard(motor_lock, response_model_cls=IgusCommandResponse)
async def reference_motor(blocking: bool = True):
    if blocking:
        response = await reference_motor_command()
        return {"success": response}
    else:
        async def async_ref():
            return await reference_motor_command()
        task_id = task_manager.create_task(async_ref())
        return MotorAsyncResponse(success=True, task_id=task_id)

@router.post(
    "/motor/fault_reset",
    response_model=Union[IgusCommandResponse, IgusAsyncResponse],
    summary="Reset motor faults",
)
@endpoint_with_lock_guard(motor_lock, response_model_cls=IgusCommandResponse)
async def reset_faults(blocking: bool = True):
    if blocking:
        response = await reset_faults_command()
        return {"success": response}
    else:
        async def async_ref():
            return await reset_faults_command()
        task_id = task_manager.create_task(async_ref())
        return MotorAsyncResponse(success=True, task_id=task_id)

@router.get(
    "/motor/position",
    response_model=IgusPositionResponse,
    summary="Get motor position",
)
@endpoint_guard(IgusPositionResponse)
async def get_motor_position():
    pos = await get_motor_position_command()
    return {"position": pos}

# @router.get(
#     "/motor/status",
#     response_model=Union[IgusStatusResponse, ErrorStatus],
#     summary="Get motor position",
# )
# @endpoint_with_lock_guard(motor_lock, Union[IgusStatusResponse, ErrorStatus])
# async def get_motor_status():
#     try:
#         data = await get_motor_status_command()
#         return IgusStatusResponse(**data)
#     except Exception as e:
#         error = {"type": type(e.args[0]).__name__, "msg": e.args[0]._message}
#         return ErrorStatus(error=error)

@router.get(
    "/motor/is_motion",
    response_model=IgusMotionResponse,
    summary="Get motor motion status",
)
@endpoint_guard(IgusMotionResponse)
async def get_motion_status():
    is_motion = await get_motor_motion_command()
    return {"is_motion": is_motion}
