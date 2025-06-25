from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional

from core.state import xarm_client, igus_client, symovo_car
from core.logger import server_logger
import drivers.xarm_scripts.xarm_positions as xarm_positions
from application.robot_scrypts import *
from core.configuration import (
    default_speed,
    ground_zero,
    zero_readypos,
    tcp_speed,
    tcp_acceleration,
    angle_speed,
    angle_acceleration
)
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
    speed:  Optional[int] = 20

@router.get("/status", response_model=Dict[str, Any])
def get_system_status():
    server_logger.log_event("info", "GET /api/system/status")
    data = {
        "symovo_online": symovo_car.online,
        "igus_connected": igus_motor.is_connected() if igus_motor else False,
    }
    server_logger.log_event("info", "System status fetched")
    return data

@router.post("/move_to_product", response_model=Dict[str, Any])
async def move_to_product(req: SystemMoveRequest):
    server_logger.log_event("info", f"POST /api/system/move_to_product {req}")
    speed = req.speed
    if speed>100:speed=100
    if speed<0:speed=1
    igus_result = None
    robot_result = None
    agv_result = None
    try:
        await check_devices_ready()
        await transport_position(speed)
        agv_result = symovo_car.move_to(
            req.location.x,
            req.location.y,
            req.location.theta,
            req.location.map_id,
            speed,
            True
        )
        # time.sleep(10)
        if agv_result is None:
            raise HTTPException(status_code=500, detail="Failed to move AGV")

        if req.lift_position is not None:
            async with igus_client as _igus_client:
                igus_result = await _igus_client.move_to_position(int(req.lift_position),speed, speed, False)
                if not igus_result.get("success", False):
                    error_msg = igus_result.get("error", "Igus move failed")
                    server_logger.log_event("info", f"Igus movement failed: {error_msg}")
                    raise Exception(error_msg)
                    
        if req.manipulator_coords:
                await changePosition(None,xarm_positions.poses["READY_SECTION_CENTER"],speed)
                async with xarm_client as client:
                    robot_result = await client.move_tool_position(req.manipulator_coords.x,req.manipulator_coords.y,req.manipulator_coords.z,angle_speed=speed,)
                    if not robot_result:
                        raise Exception("Robot movement failed")

    except Exception as e:
        server_logger.log_event("error", f"System move_to_product failed: {e}")
        raise HTTPException(status_code=500, detail=f"detail: {e}")

    server_logger.log_event("info", "System move_to_product executed")

    return {
        "success": True,
        "agv_result": agv_result,
        "lift_result": igus_result,
        "manipulator_result": robot_result,
    }

