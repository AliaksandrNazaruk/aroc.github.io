"""Symovo AGV API routes for jobs, map retrieval and pose control."""

import asyncio
import uuid
from fastapi import APIRouter, HTTPException, status, Query
from pydantic import BaseModel, Field
from typing import Any, Optional, Union, List, Dict
from collections import OrderedDict

from core.state import symovo_car
from core.logger import server_logger

class AgvPose(BaseModel):
    """Pose of the AGV on a map."""

    x: float = Field(..., description="X coordinate in meters", example=0.0)
    y: float = Field(..., description="Y coordinate in meters", example=0.0)
    theta: float = Field(..., description="Orientation in radians", example=0.0)
    map_id: Optional[str] = Field(
        None,
        description="Map identifier for the pose",
        example="warehouse",
    )


class AgvVelocity(BaseModel):
    """Velocity components of the AGV."""

    x: float = Field(..., description="Linear velocity X", example=0.0)
    y: float = Field(..., description="Linear velocity Y", example=0.0)
    theta: float = Field(..., description="Angular velocity", example=0.0)


class SymovoStateResponse(BaseModel):
    """Current status information returned by the AGV."""

    online: bool = Field(..., description="True if AGV is connected", example=True)
    last_update_time: Optional[str] = Field(
        None,
        description="Timestamp of last received update",
        example="2024-01-01T12:00:00Z",
    )
    id: Optional[str] = Field(None, description="AGV identifier", example="agv01")
    name: Optional[str] = Field(None, description="AGV name", example="AGV 1")
    pose: AgvPose
    velocity: AgvVelocity
    state: Optional[str] = Field(None, description="Current state", example="IDLE")
    battery_level: Optional[float] = Field(
        None, description="Battery level in percent", example=90.0
    )
    state_flags: Optional[Any] = Field(None, description="Internal state flags")
    robot_ip: Optional[str] = Field(None, description="AGV IP address")
    replication_port: Optional[int] = Field(None, description="Replication port")
    api_port: Optional[int] = Field(None, description="API port")
    iot_port: Optional[int] = Field(None, description="IoT port")
    last_seen: Optional[str] = Field(None, description="Last seen time")
    enabled: Optional[bool] = Field(None, description="True if AGV is enabled")
    last_update: Optional[float] = Field(None, description="Raw last update epoch")
    attributes: Optional[Any] = Field(None, description="Additional attributes")
    planned_path_edges: Optional[Any] = Field(
        None, description="Currently planned path edges"
    )


class NewJobResponse(BaseModel):
    """Response returned when a new job is started."""

    status: str = Field(..., description="Operation status", example="ok")
    message: str = Field(..., description="Human readable status message")
    result: Any = Field(..., description="Result returned by the AGV")


class GenericResult(BaseModel):
    """Simple wrapper for status result."""

    status: str = Field(..., description="Operation status", example="ok")
    result: Any = Field(..., description="Returned result object")

class MoveToPoseRequest(BaseModel):
    """Pose parameters used when commanding the AGV."""

    x: float = Field(
        ...,
        description="Target X position in meters",
        json_schema_extra={"example": 1.0},
    )
    y: float = Field(
        ...,
        description="Target Y position in meters",
        json_schema_extra={"example": 2.0},
    )
    theta: float = Field(
        0,
        description="Target orientation in radians",
        json_schema_extra={"example": 0.0},
    )
    map_id: Optional[str] = Field(
        None,
        description="Target map identifier",
        json_schema_extra={"example": "warehouse"},
    )
    max_speed: Optional[float] = Field(
        None,
        description="Maximum travel speed in m/s",
        json_schema_extra={"example": 0.5},
    )


router = APIRouter(
    prefix="/api/v1/symovo_car",
    tags=["Symovo AGV"],
    responses={
        500: {"description": "Internal error"},
    },
)

symovo_car_lock = asyncio.Lock()


@router.get(
    "/data",
    response_model=SymovoStateResponse,
    summary="Get current Symovo AGV state",
    description="Returns all current state information about the Symovo AGV.",
)
def get_system_data() -> SymovoStateResponse:
    """Get current Symovo car state."""
    server_logger.log_event("debug", "GET /api/symovo_car/data")
    last_update_str = (
        str(symovo_car.last_update_time) if symovo_car.last_update_time else None
    )
    data = {
        "online": symovo_car.online,
        "last_update_time": last_update_str,
        "id": symovo_car.id,
        "name": symovo_car.name,
        "pose": {
            "x": symovo_car.pose_x,
            "y": symovo_car.pose_y,
            "theta": symovo_car.pose_theta,
            "map_id": symovo_car.pose_map_id,
        },
        "velocity": {
            "x": symovo_car.velocity_x,
            "y": symovo_car.velocity_y,
            "theta": symovo_car.velocity_theta,
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
        "planned_path_edges": symovo_car.planned_path_edges,
    }
    server_logger.log_event("debug", "Symovo data fetched")
    return SymovoStateResponse(**data)



@router.get(
    "/jobs",
    response_model=List[Dict[str, Any]],
    summary="Get active jobs",
    description="Get a list of all current jobs on Symovo AGV.",
)
def get_symovo_car_jobs() -> List[Dict[str, Any]]:
    """Get current Symovo car jobs."""
    server_logger.log_event("info", "GET /api/symovo_car/jobs")
    jobs = symovo_car.get_jobs()
    server_logger.log_event("info", "Symovo jobs fetched")
    return jobs


@router.get(
    "/new_job",
    response_model=NewJobResponse,
    summary="Create new job by position name",
    description="Starts a new job to move AGV to the specified named position.",
)

def create_new_job(name: str = Query(..., description="Target position name")) -> NewJobResponse:

    """Start a new job that moves the AGV to a named position."""
    server_logger.log_event("info", f"GET /api/symovo_car/new_job {name}")
    result = symovo_car.go_to_position(name, True, True)
    server_logger.log_event("info", f"Symovo new job started: {name}")

    return NewJobResponse(status="ok", message=f"Going to position {name}", result=result)



@router.get(
    "/maps",
    response_model=List[str],
    summary="Get available maps",
    description="Returns a list of available maps for the AGV.",
)

def get_maps() -> List[str]:

    """Return a list of maps available on the AGV."""
    server_logger.log_event("info", "GET /api/symovo_car/maps")
    maps = symovo_car.get_maps()
    if maps is None:
        raise HTTPException(status_code=500, detail="Failed to get maps")
    server_logger.log_event("info", "Symovo maps fetched")
    return maps


@router.post(
    "/go_to_pose",
    response_model=GenericResult,
    summary="Send AGV to pose",
    description="Send the AGV to an arbitrary pose on the specified map.",
    response_description="Result of the go_to_pose command.",
)

def go_to_pose(req: MoveToPoseRequest) -> GenericResult:

    """Send the AGV to an arbitrary pose."""
    server_logger.log_event("info", f"POST /api/symovo_car/go_to_pose {req}")
    result = symovo_car.move_to(req.x, req.y, req.theta, req.map_id, req.max_speed)
    if result is None:
        raise HTTPException(status_code=500, detail="Failed to send move command")
    server_logger.log_event("info", "Symovo go_to_pose executed")
    return GenericResult(status="ok", result=result)



@router.post(
    "/check_pose",
    response_model=GenericResult,
    summary="Check pose reachability",
    description="Check if a given pose is reachable by the AGV.",
    response_description="Reachability result.",
)

def check_pose(req: MoveToPoseRequest) -> GenericResult:

    """Check if the AGV can reach the specified pose."""
    server_logger.log_event("info", f"POST /api/symovo_car/check_pose {req}")
    result = symovo_car.check_reachability(req.x, req.y, req.theta, req.map_id)
    if result is None:
        raise HTTPException(status_code=500, detail="Failed to check pose")
    server_logger.log_event("info", "Symovo pose checked")
    return GenericResult(status="ok", result=result)



@router.get(
    "/task_status",
    response_model=GenericResult,
    summary="Get status of a task",
    description="Returns the status of a running task by its ID.",
)

def task_status(task_id: str = Query(..., description="Task ID")) -> GenericResult:

    """Get progress information for a running job."""
    server_logger.log_event("info", f"GET /api/symovo_car/task_status {task_id}")
    result = symovo_car.get_task_status(task_id)
    if result is None:
        raise HTTPException(status_code=500, detail="Failed to get task status")
    server_logger.log_event("info", "Symovo task status fetched")
    return GenericResult(status="ok", result=result)
