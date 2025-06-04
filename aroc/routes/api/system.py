from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional

from core.state import symovo_car, igus_motor, xarm_client

router = APIRouter(prefix="/api/system", tags=["system"])

class ProductLocation(BaseModel):
    x: float
    y: float
    theta: float = 0
    map_id: Optional[str] = None


class ManipulatorCoords(BaseModel):
    x: float
    y: float
    z: float


class SystemMoveRequest(BaseModel):
    product_id: str
    location: ProductLocation
    lift_position: Optional[int] = None
    manipulator_coords: Optional[ManipulatorCoords] = None
    angle_speed: float = 20.0

@router.get("/status", response_model=Dict[str, Any])
def get_system_status():
    return {
        "symovo_online": symovo_car.online,
        "igus_connected": igus_motor.is_connected() if igus_motor else False,
    }

@router.post("/move_to_product", response_model=Dict[str, Any])
async def move_to_product(req: SystemMoveRequest):
    agv_result = symovo_car.move_to(
        req.location.x,
        req.location.y,
        req.location.theta,
        req.location.map_id,
    )
    if agv_result is None:
        raise HTTPException(status_code=500, detail="Failed to move AGV")

    lift_result = None
    if req.lift_position is not None and igus_motor:
        try:
            lift_result = igus_motor.move_to_position(req.lift_position)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Lift move failed: {e}")

    manip_result = None
    if req.manipulator_coords:
        try:
            manip_result = await xarm_client.move_tool_position(
                req.manipulator_coords.x,
                req.manipulator_coords.y,
                req.manipulator_coords.z,
                angle_speed=req.angle_speed,
            )
            if not manip_result.get("success", False):
                raise Exception(manip_result.get("error", "Unknown error"))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Manipulator move failed: {e}")

    return {
        "status": "ok",
        "agv_result": agv_result,
        "lift_result": lift_result,
        "manipulator_result": manip_result,
    }

