"""xArm manipulator API routes for motion, gripper control and status."""

import asyncio
import uuid
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from fastapi.concurrency import run_in_threadpool
from typing import Any, Callable, Dict, Optional
from core.logger import server_logger
from core.state import xarm_manager
from typing import Union
from typing import List, Dict
from collections import OrderedDict


router = APIRouter(prefix="/api/v1/xarm", tags=["xArm Manipulator"])

# Ensures that only one manipulator command executes at a time
manipulator_lock = asyncio.Lock()


class TaskManager:
    """Utility for tracking asynchronous manipulator tasks."""

    def __init__(self, max_tasks: int = 100):
        self.tasks: "OrderedDict[str, dict]" = OrderedDict()
        self.max_tasks = max_tasks

    def create_task(self, coro):
        """Register and start an asynchronous task."""
        task_id = str(uuid.uuid4())
        loop = asyncio.get_event_loop()
        task = loop.create_task(coro)
        self.tasks[task_id] = {
            "status": "working",  # task started
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

        # Limit task queue size
        while len(self.tasks) > self.max_tasks:
            self.tasks.popitem(last=False)
        return task_id

    def get_status(self, task_id):
        """Return information about an async task."""
        if task_id not in self.tasks:
            return {"status": "not_found"}
        task_info = self.tasks[task_id]
        return {
            "status": task_info["status"],
            "result": task_info["result"],
        }


task_manager = TaskManager()


class TaskStatusResponse(BaseModel):
    status: str
    result: Optional[Any] = None


@router.get("/manipulator/task_status/{task_id}", response_model=TaskStatusResponse)
async def get_motor_task_status(task_id: str):
    """Return status information for a previously started async manipulator task."""
    status = task_manager.get_status(task_id)
    return status


class XarmJointsDict(BaseModel):
    j1: float
    j2: float
    j3: float
    j4: float
    j5: float
    j6: float


class XarmMoveWithToolParams(BaseModel):
    x_offset: float = Field(
        ...,
        ge=-1000.0,
        le=1000.0,
        description="X offset for Tool in mm (-1000..1000.0)",
        json_schema_extra={"example": 0},
    )
    y_offset: float = Field(
        ...,
        ge=-1000.0,
        le=1000.0,
        description="Y offset for Tool in mm (-1000..1000.0)",
        json_schema_extra={"example": 0},
    )
    z_offset: float = Field(
        ...,
        ge=-1000.0,
        le=1000.0,
        description="Z offset for Tool in mm (-1000..1000.0)",
        json_schema_extra={"example": 0},
    )
    velocity: float = Field(
        ...,
        ge=0,
        le=100.0,
        description="Manipulator speed in percents (0..100.0)",
        json_schema_extra={"example": 0},
    )
    reset_faults: bool = Field(
        False,
        description="Resetting errors and reinitializing the manipulator before movement, the task execution will last 3-5 seconds longer)",
        json_schema_extra={"example": False},
    )
    blocking: bool = Field(
        True,
        description="Wait until move is complete (true: wait for completion before returning response, false: return immediately)",
        json_schema_extra={"example": True},
    )


class XarmMoveWithPoseParams(BaseModel):
    pose_name: str = Field(
        "READY_SECTION_CENTER",
        description="Сhange the pose of the manipulator to a previously saved position",
        json_schema_extra={"example": "READY_SECTION_CENTER"},
    )
    velocity: float = Field(
        ...,
        ge=0,
        le=100.0,
        description="Manipulator speed in percents (0..100.0)",
        json_schema_extra={"example": 0},
    )
    reset_faults: bool = Field(
        False,
        description="Resetting errors and reinitializing the manipulator before movement, the task execution will last 3-5 seconds longer)",
        json_schema_extra={"example": False},
    )
    blocking: bool = Field(
        True,
        description="Wait until move is complete (true: wait for completion before returning response, false: return immediately)",
        json_schema_extra={"example": True},
    )


class XarmMoveWithJointsParams(BaseModel):
    j1: float = Field(
        ...,
        ge=-500.0,
        le=500.0,
        description="Manipulator j1 position (-500.0..500.0)",
        json_schema_extra={"example": 0},
    )
    j2: float = Field(
        ...,
        ge=-500.0,
        le=500.0,
        description="Manipulator j2 position (-500.0..500.0)",
        json_schema_extra={"example": 0},
    )
    j3: float = Field(
        ...,
        ge=-500.0,
        le=500.0,
        description="Manipulator j3 position (-500.0..500.0)",
        json_schema_extra={"example": 0},
    )
    j4: float = Field(
        ...,
        ge=-500.0,
        le=500.0,
        description="Manipulator j4 position (-500.0..500.0)",
        json_schema_extra={"example": 0},
    )
    j5: float = Field(
        ...,
        ge=-500.0,
        le=500.0,
        description="Manipulator j5 position (-500.0..500.0)",
        json_schema_extra={"example": 0},
    )
    j6: float = Field(
        ...,
        ge=-500.0,
        le=500.0,
        description="Manipulator j6 position (-500.0..500.0)",
        json_schema_extra={"example": 0},
    )
    velocity: float = Field(
        ...,
        ge=0,
        le=100.0,
        description="Manipulator speed in percents (0..100.0)",
        json_schema_extra={"example": 0},
    )
    reset_faults: bool = Field(
        False,
        description="Resetting errors and reinitializing the manipulator before movement, the task execution will last 3-5 seconds longer)",
        json_schema_extra={"example": False},
    )
    blocking: bool = Field(
        True,
        description="Wait until move is complete (true: wait for completion before returning response, false: return immediately)",
        json_schema_extra={"example": True},
    )


class XarmMoveWithJointsDictParams(BaseModel):
    points: List[XarmJointsDict] = Field(
        ...,
        description="List of joints positions, each as a dict with keys 'j1'..'j6'",
        example=[
            {"j1": 0, "j2": 10, "j3": 20, "j4": 30, "j5": 40, "j6": 50},
            {"j1": 10, "j2": 20, "j3": 30, "j4": 40, "j5": 50, "j6": 60},
        ],
    )
    velocity: float = Field(
        ...,
        ge=0,
        le=100.0,
        description="Manipulator speed in percents (0..100.0)",
        example=50.0,
    )
    reset_faults: bool = Field(
        False,
        description="Resetting errors and reinitializing the manipulator before movement, the task execution will last 3-5 seconds longer)",
        example=False,
    )
    blocking: bool = Field(
        True,
        description="Wait until move is complete (true: wait for completion before returning response, false: return immediately)",
        example=True,
    )


class XarmCommandResponse(BaseModel):
    success: bool = Field(
        ..., description="True if command completed successfully", example=True
    )


class XarmAsyncResponse(BaseModel):
    success: bool = Field(..., example=True)
    task_id: str = Field(..., example="123e4567-e89b-12d3-a456-426614174000")


class XarmStatusResponse(BaseModel):
    """Status information returned by the manipulator controller."""

    alive: bool = Field(..., description="Controller heartbeat flag", example=True)
    connected: bool = Field(..., description="True if xArm is connected", example=False)
    state: int = Field(..., description="Internal controller state code", example=0)
    has_err_warn: bool = Field(
        ..., description="True if warnings or errors present", example=True
    )
    has_error: bool = Field(
        ..., description="True if an error is active", example=False
    )
    has_warn: bool = Field(
        ..., description="True if warnings are present", example=True
    )
    error_code: int = Field(..., description="Current error code", example=0)


class XarmJointsPositionResponse(BaseModel):
    """Current joint angles reported by the manipulator."""

    joints: Optional[Any] = Field(
        ...,
        description="Dictionary of joint angles in degrees",
        example={"j1": 0, "j2": 0, "j3": 0, "j4": 0, "j5": 0, "j6": 0},
    )


async def guarded_manipulator_command(
    func: Callable, *args, **kwargs
) -> XarmCommandResponse:

    """Execute manipulator command ensuring exclusive access."""
    async with manipulator_lock:
        return await _execute_manipulator_command(func, *args, **kwargs)


async def _execute_manipulator_command(func: Callable, *args, **kwargs):
    """Run a manipulator command in a thread pool and return its result."""
    try:
        result = await run_in_threadpool(func, *args, **kwargs)
        if hasattr(result, "result") and hasattr(result, "done"):
            result = result.result(timeout=10)
        return result
    except Exception as e:
        server_logger.log_event("error", f"{func.__name__} failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e)
        )


@router.post(
    "/manipulator/complex_move/with_joints_dict",
    response_model=Union[XarmCommandResponse, XarmAsyncResponse],
    summary="Move manipulator by list of joint positions",
    description="""
        Move the manipulator along a path defined by a list of joint positions.<br>
        Each point is a dictionary with keys 'j1'...'j6'.<br>
        While moving, other commands are not accepted.
        """,
    responses={
        200: {"description": "Success (see returned field: success or task_id)"},
        423: {"description": "Manipulator is busy"},
        503: {"description": "Manipulator error or hardware fault"},
    },
)
async def complex_move_with_joints_dict(params: XarmMoveWithJointsDictParams):
    """Move the manipulator along a series of joint positions."""
    if manipulator_lock.locked():
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED, detail="Manipulator is busy"
        )
    try:
        robot_main = xarm_manager.get_instance(reset=params.reset_faults)
        # complex_move_with_joints expects a sequence of points and velocity
        if params.blocking:
            result = await guarded_manipulator_command(
                robot_main.complex_move_with_joints, params
            )
            return XarmCommandResponse(success=result)
        else:

            async def async_move():
                return await guarded_manipulator_command(
                    robot_main.complex_move_with_joints, params
                )

            task_id = task_manager.create_task(async_move())
            return XarmAsyncResponse(success=True, task_id=task_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Failed to perform complex move: {str(e)}",
        )


@router.post(
    "/manipulator/move/change_joints",
    response_model=Union[XarmCommandResponse, XarmAsyncResponse],
    summary="Change manipulator pose",
    description="""
        Starts the change pose procedure for the manipulator.<br>
        <b>Note:</b> While change pose, other control commands are not accepted.<br>
        Returns HTTP 423 Locked if the motor is busy.
        """,
    response_description="Result of the change pose procedure.",
    responses={
        200: {"description": "Success (see returned field: success or task_id)"},
        423: {"description": "Manipulator is busy"},
        503: {"description": "Manipulator error or hardware fault"},
    },
)
async def change_joints(params: XarmMoveWithJointsParams):
    """Move the manipulator to the given joint angles."""
    if manipulator_lock.locked():
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED, detail="Manipulator is busy"
        )
    try:
        robot_main = xarm_manager.get_instance(reset=params.reset_faults)
        if params.blocking:
            result = await guarded_manipulator_command(
                robot_main.move_with_joints, params
            )
            return XarmCommandResponse(success=result)
        else:

            async def async_move():
                return await guarded_manipulator_command(
                    robot_main.move_with_joints, params
                )

            task_id = task_manager.create_task(async_move())
            return XarmAsyncResponse(success=True, task_id=task_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Failed to change tool position: {str(e)}",
        )


@router.post(
    "/manipulator/move/change_pose",
    response_model=Union[XarmCommandResponse, XarmAsyncResponse],
    summary="Change manipulator pose",
    description="""
        Starts the change pose procedure for the manipulator.<br>
        <b>Note:</b> While change pose, other control commands are not accepted.<br>
        Returns HTTP 423 Locked if the motor is busy.
        """,
    response_description="Result of the change pose procedure.",
    responses={
        200: {"description": "Success (see returned field: success or task_id)"},
        423: {"description": "Manipulator is busy"},
        503: {"description": "Manipulator error or hardware fault"},
    },
)
async def change_pose(params: XarmMoveWithPoseParams):
    """Move the manipulator to a named pose."""
    if manipulator_lock.locked():
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED, detail="Manipulator is busy"
        )
    try:
        robot_main = xarm_manager.get_instance(reset=params.reset_faults)
        if params.blocking:
            result = await guarded_manipulator_command(robot_main.move_to_pose, params)
            return XarmCommandResponse(success=result)
        else:

            async def async_move():
                return await guarded_manipulator_command(
                    robot_main.move_to_pose, params
                )

            task_id = task_manager.create_task(async_move())
            return XarmAsyncResponse(success=True, task_id=task_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Failed to change tool position: {str(e)}",
        )


@router.post(
    "/manipulator/move/change_tool_position",
    response_model=Union[XarmCommandResponse, XarmAsyncResponse],
    summary="Change manipulator tool position",
    description="""
        Starts the change tool position procedure for the manipulator.<br>
        <b>Note:</b> While change tool position, other control commands are not accepted.<br>
        Returns HTTP 423 Locked if the motor is busy.
        """,
    response_description="Result of the change tool position procedure.",
    responses={
        200: {"description": "Success (see returned field: success or task_id)"},
        423: {"description": "Manipulator is busy"},
        503: {"description": "Manipulator error or hardware fault"},
    },
)
async def change_tool_position(params: XarmMoveWithToolParams):
    """Adjust tool position using provided offsets."""
    if manipulator_lock.locked():
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED, detail="Manipulator is busy"
        )
    try:
        robot_main = xarm_manager.get_instance(reset=params.reset_faults)
        if params.blocking:
            result = await guarded_manipulator_command(
                robot_main.move_tool_position, params
            )
            return XarmCommandResponse(success=result)
        else:

            async def async_move():
                return await guarded_manipulator_command(
                    robot_main.move_tool_position, params
                )

            task_id = task_manager.create_task(async_move())
            return XarmAsyncResponse(success=True, task_id=task_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Failed to change tool position: {str(e)}",
        )


@router.post(
    "/manipulator/drop",
    response_model=XarmCommandResponse,
    summary="Gripper disable",
    description="""
        Starts gripper disable procedure for the manipulator.<br>
        Returns HTTP 423 Locked if the manipulator is busy.
        """,
    response_description="Result of the gripper disable procedure.",
    responses={
        200: {"description": "Gripper successfully disabled"},
        423: {"description": "Manipulator is busy"},
        503: {"description": "Manipulator error or hardware fault"},
    },
)
async def gripper_drop():
    """Release the object currently held by the gripper."""
    if manipulator_lock.locked():
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED, detail="Manipulator is busy"
        )
    try:
        robot_main = xarm_manager.get_instance()
        result = robot_main.drop()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Failed to disable gripper: {str(e)}",
        )
    return XarmCommandResponse(success=result)


@router.post(
    "/manipulator/take",
    response_model=XarmCommandResponse,
    summary="Gripper enable",
    description="""
        Starts gripper enable procedure for the manipulator.<br>
        Returns HTTP 423 Locked if the manipulator is busy.
        """,
    response_description="Result of the gripper enable procedure.",
    responses={
        200: {"description": "Gripper successfully enabled"},
        423: {"description": "Manipulator is busy"},
        503: {"description": "Manipulator error or hardware fault"},
    },
)
async def gripper_take():
    """Close the gripper to take an object."""
    if manipulator_lock.locked():
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED, detail="Manipulator is busy"
        )
    try:
        robot_main = xarm_manager.get_instance()
        result = robot_main.take()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Failed to enable gripper: {str(e)}",
        )
    return XarmCommandResponse(success=result)


@router.get(
    "/manipulator/fault_reset",
    response_model=XarmStatusResponse,
    summary="Reset manipulator faults",
    description="""
        Resets fault states on the manipulator controller.<br>
        <b>Note:</b> While resetting faults, other control commands are not accepted.<br>
        Returns HTTP 423 Locked if the manipulator is busy.
        """,
    response_description="Result of the fault reset operation.",
    responses={
        200: {"description": "Manipulator faults successfully reset"},
        423: {"description": "Manipulator is busy"},
        503: {"description": "Manipulator error or hardware fault"},
    },
)
async def reset_faults():
    """Reset error state on the manipulator controller."""
    if manipulator_lock.locked():
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED, detail="Manipulator is busy"
        )
    try:
        xarm_manager._create_new_instance()
        robot_main = xarm_manager.get_instance()
        result = robot_main.get_status()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Failed to get manipulator status: {str(e)}",
        )
    return XarmStatusResponse(
        alive=result["alive"],
        connected=result["connected"],
        state=result["state"],
        has_err_warn=result["has_err_warn"],
        has_error=result["has_error"],
        has_warn=result["has_warn"],
        error_code=result["error_code"],
    )


@router.get(
    "/manipulator/status",
    response_model=XarmStatusResponse,
    summary="Get manipulator status",
    description="""
        Returns the current status of the manipulator.<br>
        If the manipulator is busy executing another command, returns HTTP 423 Locked.
        """,
    response_description="Current status of the manipulator.",
    responses={
        200: {"description": "Status retrieved"},
        423: {"description": "Manipulator is busy"},
        503: {"description": "Error retrieving manipulator status"},
    },
)
async def get_manipulator_status():
    """Return current manipulator status information."""
    if manipulator_lock.locked():
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED, detail="Manipulator is busy"
        )
    try:
        robot_main = xarm_manager.get_instance()
        result = robot_main.get_status()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Failed to get manipulator status: {str(e)}",
        )
    return XarmStatusResponse(
        alive=result["alive"],
        connected=result["connected"],
        state=result["state"],
        has_err_warn=result["has_err_warn"],
        has_error=result["has_error"],
        has_warn=result["has_warn"],
        error_code=result["error_code"],
    )


@router.get(
    "/manipulator/current_position",
    response_model=Optional[dict],
    summary="Get manipulator current position",
    description="""
        Returns the current position of the manipulator.<br>
        If the manipulator is busy executing another command, returns HTTP 423 Locked.
        """,
    response_description="Current position of the manipulator.",
    responses={
        200: {"description": "Current position retrieved"},
        423: {"description": "Manipulator is busy"},
        503: {"description": "Error retrieving manipulator current position"},
    },
)
async def get_current_position():
    """Fetch the current named pose and joint positions."""
    if manipulator_lock.locked():
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED, detail="Manipulator is busy"
        )
    try:
        robot_main = xarm_manager.get_instance()
        result = robot_main.get_current_position()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Failed to get manipulator status: {str(e)}",
        )
    return {"pose_name": result[0], "points": result[1]}


@router.get(
    "/manipulator/joints_position",
    response_model=XarmJointsPositionResponse,
    summary="Get manipulator joints position",
    description="""
        Returns the current joints position of the manipulator.<br>
        If the manipulator is busy executing another command, returns HTTP 423 Locked.
        """,
    response_description="Current joints position of the manipulator.",
    responses={
        200: {"description": "Joints position retrieved"},
        423: {"description": "Manipulator is busy"},
        503: {"description": "Error retrieving manipulator joints position"},
    },
)
async def get_manipulator_joints_position():
    """Return the current joint angles of the manipulator."""
    if manipulator_lock.locked():
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED, detail="Manipulator is busy"
        )
    try:
        robot_main = xarm_manager.get_instance()
        result = robot_main.get_joints_position()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Failed to get manipulator status: {str(e)}",
        )
    return XarmJointsPositionResponse(joints=result[1])


@router.get(
    "/health",
    summary="Check API health",
    description="Healthcheck endpoint that returns a simple status.",
)
async def healthcheck():
    """
    Healthcheck endpoint.
    """
    return {"status": "ok"}
