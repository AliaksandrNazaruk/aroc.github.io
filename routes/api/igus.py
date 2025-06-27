"""
Igus Motor API

- Absolute and relative movement
- Homing (reference)
- Fault reset
- Status monitoring
- Async task support
"""

import asyncio
import uuid
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from fastapi.concurrency import run_in_threadpool
from typing import Any, Callable, Dict, Optional
from core.logger import server_logger
from typing import Union
from collections import OrderedDict

router = APIRouter(
    prefix="/api/v1/igus",
    tags=["Igus Motor"]
)

motor_lock = asyncio.Lock()

class TaskManager:
    def __init__(self, max_tasks: int = 100):
        self.tasks: "OrderedDict[str, dict]" = OrderedDict()
        self.max_tasks = max_tasks

    def create_task(self, coro):
        task_id = str(uuid.uuid4())
        loop = asyncio.get_event_loop()
        task = loop.create_task(coro)
        self.tasks[task_id] = {
            "status": "working",  # задача запущена
            "result": None,
            "task": task,
        }

        def _on_task_done(t: asyncio.Task):
            try:
                res = t.result()
                self.tasks[task_id]["status"] = "done"
                self.tasks[task_id]["result"] = res
            except Exception as e:
                self.tasks[task_id]["status"] = "error"
                self.tasks[task_id]["result"] = str(e)

        task.add_done_callback(_on_task_done)

        # Ограничиваем размер очереди
        while len(self.tasks) > self.max_tasks:
            self.tasks.popitem(last=False)
        return task_id

    def get_status(self, task_id):
        if task_id not in self.tasks:
            return {"status": "not_found"}
        task_info = self.tasks[task_id]
        return {
            "status": task_info["status"],
            "result": task_info["result"]
        }

task_manager = TaskManager()

class TaskStatusResponse(BaseModel):
    status: str
    result: Optional[Any] = None

@router.get("/motor/task_status/{task_id}", response_model=TaskStatusResponse)
async def get_motor_task_status(task_id: str):
    status = task_manager.get_status(task_id)
    return status

class MotorMoveParams(BaseModel):
    position: int = Field(
        ...,
        ge=0, le=120_000,
        description="Target position in encoder units (0..120000)",
        json_schema_extra={"example": 5000}
    )
    velocity: int = Field(
        5000,
        ge=0, le=10_000,
        description="Motion velocity (0..10000)",
        json_schema_extra={"example": 5000}
    )
    acceleration: int = Field(
        5000,
        ge=0, le=10_000,
        description="Motion acceleration (0..10000)",
        json_schema_extra={"example": 5000}
    )
    blocking: bool = Field(
        True,
        description="Wait until move is complete (true: wait for completion before returning response, false: return immediately)",
        json_schema_extra={"example": True}
    )

class MotorCommandResponse(BaseModel):
    success: bool = Field(..., description="True if command completed successfully", example=True)

class MotorAsyncResponse(BaseModel):
    success: bool = Field(..., example=True)
    task_id: str = Field(..., example="123e4567-e89b-12d3-a456-426614174000")

class MotorStatusResponse(BaseModel):
    status: int = Field(..., description="Status word of the motor controller", example=8192)
    homing: bool = Field(..., description="True if motor is homed", example=True)
    error: bool = Field(..., description="True if error is present", example=False)
    connected: bool = Field(..., description="True if motor is connected", example=True)
    position: int = Field(..., description="Current position in encoder units", example=10000)

async def guarded_motor_command(func: Callable, *args, **kwargs) -> MotorCommandResponse:
    if motor_lock.locked():
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail="Motor is busy"
        )
    async with motor_lock:
        return await _execute_motor_command(func, *args, **kwargs)

async def _execute_motor_command(func: Callable, *args, **kwargs):
    try:
        result = await run_in_threadpool(func, *args, **kwargs)
        if hasattr(result, 'result') and hasattr(result, 'done'):
            result = result.result(timeout=10)  # или без timeout
        return result
    except Exception as e:
        server_logger.log_event("error", f"{func.__name__} failed: {e}")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE,detail=str(e))

@router.post(
    "/motor/move",
    response_model=Union[MotorCommandResponse, MotorAsyncResponse],
    summary="Move motor",
    description="""
        Moves the motor to the specified position.<br>
        <b>Note:</b> While moving, other control commands are not accepted.<br>
        <ul>
            <li><b>position</b>: Target absolute position (0..120000)</li>
            <li><b>velocity</b>: Motion velocity (0..10000)</li>
            <li><b>acceleration</b>: Motion acceleration (0..10000)</li>
            <li><b>wait</b>: Wait until the move is finished</li>
        </ul>
        Returns HTTP 423 Locked if the motor is busy.
        """,
    response_description="Result of the move command.",
    responses={
        200: {"description": "Success (see returned field: success or task_id)"},
        423: {"description": "Motor is busy"},
        503: {"description": "Motor error or hardware fault"},
        422: {"description": "Validation error"},
    }
)
async def move_motor(params: MotorMoveParams):
    from core.state import igus_motor
    if motor_lock.locked():
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail="Motor is busy"
        )
    try:
        if params.blocking:
            response = await guarded_motor_command(igus_motor.move_to_position,target_position=params.position,velocity=params.velocity,acceleration=params.acceleration,blocking=True,)
            return MotorCommandResponse(success=response)
        else:
            async def async_move():
                return await guarded_motor_command(igus_motor.move_to_position,target_position=params.position,velocity=params.velocity,acceleration=params.acceleration,blocking=True,)
            task_id = task_manager.create_task(async_move())
            return MotorAsyncResponse(success=True, task_id=task_id)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE,detail=f"Motor fault reset failed: {str(e)}")
    
@router.post(
    "/motor/reference",
    response_model=Union[MotorCommandResponse, MotorAsyncResponse],
    summary="Home (reference) motor",
    description="""
        Starts the homing (reference) procedure for the motor.<br>
        <b>Note:</b> While homing, other control commands are not accepted.<br>
        Returns HTTP 423 Locked if the motor is busy.
        """,
    response_description="Result of the homing procedure.",
    responses={
        200: {"description": "Success (see returned field: success or task_id)"},
        423: {"description": "Motor is busy"},
        503: {"description": "Motor error or hardware fault"},
    }
)
async def reference_motor(blocking: bool = True):
    from core.state import igus_motor
    if motor_lock.locked():
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail="Motor is busy"
        )
    try:
        if blocking:
            response = await guarded_motor_command(igus_motor.home)
            return MotorCommandResponse(success=response)
        else:
            async def async_ref():
                return await guarded_motor_command(igus_motor.home)
            task_id = task_manager.create_task(async_ref())
            return MotorAsyncResponse(success=True, task_id=task_id)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE,detail=f"Motor fault reset failed: {str(e)}")

@router.post(
    "/motor/fault_reset",
    response_model=Union[MotorCommandResponse, MotorAsyncResponse],
    summary="Reset motor faults",
    description="""
        Resets fault states on the motor controller.<br>
        <b>Note:</b> While resetting faults, other control commands are not accepted.<br>
        Returns HTTP 423 Locked if the motor is busy.
        """,
    response_description="Result of the fault reset operation.",
    responses={
        200: {"description": "Success (see returned field: success or task_id)"},
        423: {"description": "Motor is busy"},
        503: {"description": "Motor error or hardware fault"},
    }
)
async def reset_faults(blocking: bool = True):
    """Resets faults on the Igus motor and returns the result."""
    from core.state import igus_motor
    if motor_lock.locked():
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail="Motor is busy"
        )
    try:
        if blocking:
            response = await guarded_motor_command(igus_motor.fault_reset)
            return MotorCommandResponse(success=response)
        else:
            async def async_ref():
                return await guarded_motor_command(igus_motor.fault_reset)
            task_id = task_manager.create_task(async_ref())
            return MotorAsyncResponse(success=True, task_id=task_id)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE,detail=f"Motor fault reset failed: {str(e)}")

@router.get(
    "/motor/status",
    response_model=MotorStatusResponse,
    summary="Get motor status",
    description="""
        Returns the current status of the motor.<br>
        If the motor is busy executing another command, returns HTTP 423 Locked.
        """,
    response_description="Current status of the motor.",
    responses={
        200: {"description": "Status retrieved"},
        423: {"description": "Motor is busy"},
        503: {"description": "Error retrieving motor status"},
    }
)
async def get_motor_status() -> MotorStatusResponse:
    from core.state import igus_motor
    if motor_lock.locked():
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail="Motor is busy"
        )
    try:
        result = await run_in_threadpool(igus_motor.get_status)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Failed to get motor status: {str(e)}"
        )
    return MotorStatusResponse(
        status=result["statusword"],
        homing=result["homed"],
        error=result["error_state"],
        connected=result["connected"],
        position=result["position"],
    )

@router.get(
    "/health",
    summary="Check API health",
    description="Healthcheck endpoint that returns a simple status."
)
async def healthcheck():
    """
    Healthcheck endpoint.
    """
    return {"status": "ok"}

