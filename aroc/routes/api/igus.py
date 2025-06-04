# routes/api/igus_persistent.py

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
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

@router.post("/move_to_position", response_model=MotorCommandResponse)
async def move_motor(params: MoveParams):
    from core.state import igus_motor
    try:
        await run_in_threadpool(
            igus_motor.move_to_position,
            target_position=params.position,
            velocity=params.velocity,
            acceleration=params.acceleration,
            blocking=params.wait,
        )
        return {
            "success": True,
            "position": igus_motor._position,
            "state": igus_motor.get_status(),
            "error": igus_motor.get_error(),
        }
    except Exception as e:
        return {
            "success": False,
            "position": igus_motor._position,
            "state": igus_motor.get_status(),
            "error": str(e),
        }

@router.post("/reference", response_model=MotorCommandResponse)
async def reference_motor():
    from core.state import igus_motor
    try:
        await run_in_threadpool(igus_motor.home)
        return {
            "success": True,
            "result": {"homing": igus_motor._homed},  # included in result
            "error": igus_motor.get_error(),
            "state": igus_motor.get_status()
        }
    except Exception as e:
        return {
            "success": False,
            "result": None,
            "error": str(e),
            "state": igus_motor.get_status()
        }



@router.post("/fault_reset", response_model=MotorCommandResponse)
async def reset_faults():
    from core.state import igus_motor
    try:
        result = igus_motor.fault_reset()
        return {
            "success": bool(result),
            "result": {"fault_reset": result},
            "error": igus_motor.get_error(),
            "state": igus_motor.get_status(),
        }
    except Exception as e:
        return {
            "success": False,
            "result": None,
            "error": str(e),
            "state": igus_motor.get_status() if igus_motor else {},
        }


@router.get("/data", response_model=Dict[str, Any])
async def get_motor_data():
    from core.state import igus_motor 
    return {
        "status": igus_motor.get_status(),
        "error": igus_motor.get_error(),
        "connected": igus_motor.is_connected(),
        "position": igus_motor._position,
    }

@router.get("/state", response_model=Dict[str, Any])
async def get_motor_state():
    from core.state import igus_motor 
    return {
        "status": igus_motor.get_status(),
        "homing": igus_motor._homed,
        "error": igus_motor.get_error(),
        "connected": igus_motor.is_connected(),
        "position": igus_motor._position,
    }
