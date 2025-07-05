"""Symovo AGV API routes for jobs, map retrieval and pose control."""

import asyncio
from fastapi import APIRouter, HTTPException, Query
from typing import Any, List, Dict
from core.state import symovo_client
from core.logger import server_logger
from models.api_types import (ErrorStatus, SymovoVelocity, SymovoPose, SymovoStatusResponse,NewJobResponse,GenericResult,MoveToPoseRequest)
from typing import Union
from utils.api import endpoint_with_lock_guard, endpoint_guard

router = APIRouter(
    prefix="/api/v1/symovo_car",
    tags=["Symovo AGV"],
    responses={
        500: {"description": "Internal error"},
    },
)

symovo_car_lock = asyncio.Lock()

# @router.get(
#     "/status",
#     response_model=Union[SymovoStatusResponse, ErrorStatus],
#     summary="Get current Symovo AGV state",
#     description="Returns all current state information about the Symovo AGV.",
# )
# @endpoint_guard()
# async def get_status() -> Union[SymovoStatusResponse, ErrorStatus]:
#     data = symovo_client.get_status()
#     return data



@router.get(
    "/jobs",
    response_model=List[Dict[str, Any]],
    summary="Get active jobs",
    description="Get a list of all current jobs on Symovo AGV.",
)
def get_symovo_car_jobs() -> List[Dict[str, Any]]:
    """Get current Symovo car jobs."""
    jobs = symovo_client.get_jobs()
    return jobs

@router.get(
    "/new_job",
    response_model=NewJobResponse,
    summary="Create new job by position name",
    description="Starts a new job to move AGV to the specified named position.",
)
def create_new_job(name: str = Query(..., description="Target position name")) -> NewJobResponse:
    result = symovo_client.go_to_position(name, True, True)
    return NewJobResponse(status="ok", message=f"Going to position {name}", result=result)

@router.get(
    "/maps",
    response_model=List[str],
    summary="Get available maps",
    description="Returns a list of available maps for the AGV.",
)
def get_maps() -> List[str]:
    server_logger.log_event("info", "GET /api/symovo_car/maps")
    maps = symovo_client.get_maps()
    if maps is None:
        raise HTTPException(status_code=500, detail="Failed to get maps")
    return maps

@router.post(
    "/go_to_pose",
    response_model=GenericResult,
    summary="Send AGV to pose",
    description="Send the AGV to an arbitrary pose on the specified map.",
    response_description="Result of the go_to_pose command.",
)
def go_to_pose(req: MoveToPoseRequest) -> GenericResult:
    result = symovo_client.move_to(req.x, req.y, req.theta, req.map_id, req.max_speed)
    if result is None:
        raise HTTPException(status_code=500, detail="Failed to send move command")
    return GenericResult(status="ok", result=result)

@router.post(
    "/check_pose",
    response_model=GenericResult,
    summary="Check pose reachability",
    description="Check if a given pose is reachable by the AGV.",
    response_description="Reachability result.",
)
def check_pose(req: MoveToPoseRequest) -> GenericResult:
    result = symovo_client.check_reachability(req.x, req.y, req.theta, req.map_id)
    if result is None:
        raise HTTPException(status_code=500, detail="Failed to check pose")
    return GenericResult(status="ok", result=result)

@router.get(
    "/task_status",
    response_model=GenericResult,
    summary="Get status of a task",
    description="Returns the status of a running task by its ID.",
)
def task_status(task_id: str = Query(..., description="Task ID")) -> GenericResult:
    result = symovo_client.get_task_status(task_id)
    if result is None:
        raise HTTPException(status_code=500, detail="Failed to get task status")
    server_logger.log_event("info", "Symovo task status fetched")
    return GenericResult(status="ok", result=result)