
import asyncio
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from fastapi.concurrency import run_in_threadpool
from typing import Any, Callable, Dict, Optional
from core.logger import server_logger

router = APIRouter(
    prefix="/api/v1/igus",
    tags=["Igus Motor"]
)

motor_lock = asyncio.Lock()

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
    wait: bool = Field(
        True,
        description="Wait until move is complete (true: wait for completion before returning response, false: return immediately)",
        json_schema_extra={"example": True}
    )

class MotorCommandResponse(BaseModel):
    success: bool = Field(..., description="True if command completed successfully", example=True)
    result: bool = Field(..., description="Result of the command (meaning depends on the command)", example=True)
    error: Optional[str] = Field(None, description="Error message if the command failed", example="Motor is busy")

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

async def _execute_motor_command(func: Callable, *args, **kwargs) -> MotorCommandResponse:
    try:
        result = await run_in_threadpool(func, *args, **kwargs)
        return MotorCommandResponse(
            success=True,
            result=result,
            error=None
        )
    except Exception as e:
        server_logger.log_event("error", f"{func.__name__} failed: {e}")
        return MotorCommandResponse(
            success=False,
            result=False,
            error=str(e)
        )

@router.post(
    "/motor/move",
    response_model=MotorCommandResponse,
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
        200: {"description": "Motor successfully moved"},
        423: {"description": "Motor is busy"},
        503: {"description": "Motor error or hardware fault"},
        422: {"description": "Validation error"},
    }
)
async def move_motor(params: MotorMoveParams):
    """
    Move the motor to a specified position.
    """
    from core.state import igus_motor
    try:
        response = await guarded_motor_command(
            igus_motor.move_to_position,
            target_position=params.position,
            velocity=params.velocity,
            acceleration=params.acceleration,
            blocking=params.wait,
        )
        if not response.success:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=response.error or "Unknown motor error"
            )
        return response
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Motor move failed: {str(e)}"
        )

@router.post(
    "/motor/reference",
    response_model=MotorCommandResponse,
    summary="Home (reference) motor",
    description="""
        Starts the homing (reference) procedure for the motor.<br>
        <b>Note:</b> While homing, other control commands are not accepted.<br>
        Returns HTTP 423 Locked if the motor is busy.
        """,
    response_description="Result of the homing procedure.",
    responses={
        200: {"description": "Motor successfully referenced"},
        423: {"description": "Motor is busy"},
        503: {"description": "Motor error or hardware fault"},
    }
)
async def reference_motor():
    from core.state import igus_motor
    try:
        response = await guarded_motor_command(igus_motor.home)
        if not response.success:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=response.error or "Unknown motor error"
            )
        return response
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Motor homing failed: {str(e)}"
        )

@router.post(
    "/motor/fault_reset",
    response_model=MotorCommandResponse,
    summary="Reset motor faults",
    description="""
        Resets fault states on the motor controller.<br>
        <b>Note:</b> While resetting faults, other control commands are not accepted.<br>
        Returns HTTP 423 Locked if the motor is busy.
        """,
    response_description="Result of the fault reset operation.",
    responses={
        200: {"description": "Motor faults successfully reset"},
        423: {"description": "Motor is busy"},
        503: {"description": "Motor error or hardware fault"},
    }
)
async def reset_faults():
    """Resets faults on the Igus motor and returns the result."""
    from core.state import igus_motor
    try:
        response = await guarded_motor_command(igus_motor.fault_reset)
        if not response.success:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=response.error or "Unknown motor error"
            )
        return response
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Motor fault reset failed: {str(e)}"
        )

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
