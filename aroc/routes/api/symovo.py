# routes/api/symovo.py

from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any
from core.state import symovo_car

router = APIRouter(prefix="/api/symovo_car", tags=["symovo"])

@router.get("/data")
def get_system_data():
    """Get current Symovo car state"""
    last_update_str = str(symovo_car.last_update_time) if symovo_car.last_update_time else None

    return {
        "online": symovo_car.online,
        "last_update_time": last_update_str,
        "id": symovo_car.id,
        "name": symovo_car.name,
        "pose": {
            "x": symovo_car.pose_x,
            "y": symovo_car.pose_y,
            "theta": symovo_car.pose_theta,
            "map_id": symovo_car.pose_map_id
        },
        "velocity": {
            "x": symovo_car.velocity_x,
            "y": symovo_car.velocity_y,
            "theta": symovo_car.velocity_theta
        },
        "state": symovo_car.state,
        "battery_level": symovo_car.battery_level,
        "state_flags": symovo_car.state_flags,
        "robot_ip": symovo_car.robot_ip,
        "replication_port": symovo_car.replication_port,
        "api_port": symovo_car.api_port,
        "iot_port": symovo_car.iot_port,
        "last_seen": symovo_car.last_seen,
        "enabled": symovo_car.enabled,
        "last_update": symovo_car.last_update,
        "attributes": symovo_car.attributes,
        "planned_path_edges": symovo_car.planned_path_edges
    }

@router.get("/jobs")
def get_symovo_car_jobs():
    """Get current Symovo car jobs"""
    return symovo_car.get_jobs()

@router.get("/new_job")
def create_new_job(name: str = Query(...)):
    """Start a new job with given position name"""
    result = symovo_car.go_to_position(name, True, True)
    return {
        "status": "ok",
        "message": f"Going to position {name}",
        "result": result
    }
