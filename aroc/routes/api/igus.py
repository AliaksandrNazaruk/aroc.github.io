# routes/api/igus_persistent.py

from fastapi import APIRouter
from pydantic import BaseModel
from typing import Any, Callable, Dict, Optional

from core.logger import server_logger
from core.state import igus_motor

router = APIRouter(prefix="/api/igus", tags=["igus_persistent"])



class MoveParams(BaseModel):
    position: int
    velocity: int = 5000
    acceleration: int = 5000
    wait: bool = True

class MotorCommandResponse(BaseModel):
    success: bool
    result: Optional[Dict[str, Any]]
    error: Optional[str]
    state: Dict[str, Any]

from fastapi.concurrency import run_in_threadpool


def _build_response(success: bool, *, result: Optional[Dict[str, Any]] = None, error: Optional[str] = None) -> Dict[str, Any]:
    """Compose a standard motor command response."""
    return {
        "success": success,
        "result": result,
        "error": error,
        "state": igus_motor.get_status(),
    }


async def _execute_motor_command(func: Callable, *args, **kwargs) -> Dict[str, Any]:
    """Run a blocking motor command in a threadpool and build a response."""
    try:
        result = await run_in_threadpool(func, *args, **kwargs)
        return _build_response(True, result=result)
    except Exception as e:
        server_logger.log_event("error", f"{func.__name__} failed: {e}")
        return _build_response(False, error=str(e))

@router.post("/move_to_position", response_model=MotorCommandResponse)
async def move_motor(params: MoveParams):

    try:
        response = await _execute_motor_command(
            igus_motor.move_to_position,
            target_position=params.position,
            velocity=params.velocity,
            acceleration=params.acceleration,
            blocking=params.wait,
        )
        # expose position separately for backward compatibility
        response["result"] = {"position": igus_motor._position}
        return response
    except Exception as e:
        server_logger.log_event("error", f"move_to_position failed: {e}")
        # if e.args[0] == 'Drive reports FAULT bit set' or e.args[0] == 'Timeout waiting for state OPERATION_ENABLED':
        try:
            igus_motor._controller.initialize()
        except Exception as init_err:
            server_logger.log_event("error", f"Motor re-init failed: {init_err}")
    return

    # expose position separately for backward compatibility
    response["result"] = {"position": igus_motor._position}
    return response

@router.post("/reference", response_model=MotorCommandResponse)
async def reference_motor():
    try:
        response = await _execute_motor_command(igus_motor.home)
        response["result"] = {"homing": igus_motor._homed}
        return response
    except Exception as e:
        server_logger.log_event("error", f"reference_motor failed: {e}")
        # if e.args[0] == 'Drive reports FAULT bit set' or e.args[0] == 'Timeout waiting for state OPERATION_ENABLED':
        try:
            igus_motor._controller.initialize()
        except Exception as init_err:
            server_logger.log_event("error", f"Motor re-init failed: {init_err}")
    return

@router.post("/fault_reset", response_model=MotorCommandResponse)
async def reset_faults():
    response = await _execute_motor_command(igus_motor.fault_reset)
    # convert bool result to structured form for schema compliance
    if isinstance(response.get("result"), bool):
        response["result"] = {"fault_reset": response["result"]}
    return response


@router.get("/data", response_model=Dict[str, Any])
async def get_motor_data():
    status = igus_motor.get_status()
    return {
        "status": status['statusword'],
        "homing": status['homed'],
        "error": status['error_state'],
        "connected": status['connected'],
        "position": status['position'],
    }

@router.get("/state", response_model=Dict[str, Any])
async def get_motor_state():
    status = igus_motor.get_status()
    return {
        "status": status['statusword'],
        "homing": status['homed'],
        "error": status['error_state'],
        "connected": status['connected'],
        "position": status['position'],
    }


@router.get("/position", response_model=Dict[str, Any])
async def get_position():
    status = igus_motor.get_status()
    return {
        "status": status['statusword'],
        "homing": status['homed'],
        "error": status['error_state'],
        "connected": status['connected'],
        "position": status['position'],
    }