"""Utility routes for serving files, trajectory management and Arduino commands."""

from fastapi.responses import FileResponse, JSONResponse
from typing import Dict, Any
import os
from core.state import job_done  # indicates if long running job is finished
from fastapi import APIRouter, HTTPException, status
from db.trajectory import get_trajectory, save_trajectory

import arduino_controller.arduino_led_controller as als

router = APIRouter(tags=["misc"])


@router.get(
    "/",
    response_class=FileResponse,
    summary="Serve main page",
    description="Return the main index.html file from the server root.",
)
def get_root() -> FileResponse:
    """Serve index.html"""
    filename = "index.html"
    if not os.path.exists(filename):
        return JSONResponse(content={"error": "File not found"}, status_code=404)
    return FileResponse(filename)


@router.get(
    "/control",
    response_class=FileResponse,
    summary="Serve control page",
    description="Return the control interface HTML file.",
)
def get_control_page() -> FileResponse:
    """Serve control page"""
    filename = "index.html"
    if not os.path.exists(filename):
        return JSONResponse(content={"error": "File not found"}, status_code=404)
    return FileResponse(filename)


@router.get(
    "/api/trajectory",
    response_model=Dict[str, Any],
    summary="Get trajectory configuration",
    description="Return the currently stored trajectory configuration.",
)
def api_get_trajectory() -> Dict[str, Any]:
    """Return the currently stored trajectory configuration."""
    config = get_trajectory()
    if config is None:
        raise HTTPException(
            status_code=404, detail="Trajectory configuration not found."
        )
    return config


@router.post(
    "/api/trajectory",
    response_model=Dict[str, Any],
    status_code=status.HTTP_201_CREATED,
    summary="Save trajectory configuration",
    description="Persist a new trajectory configuration on the server.",
)
def api_save_trajectory(config: Dict[str, Any]) -> Dict[str, Any]:
    """Persist a new trajectory configuration."""
    try:
        save_trajectory(config)
        return {"status": "ok", "message": "Trajectory configuration saved."}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/job_status",
    response_model=Dict[str, Any],
    summary="Get job status",
    description="Return whether the background job has finished.",
)
def get_job_status() -> Dict[str, Any]:
    """Get current job status"""
    return {"done": job_done}


@router.get(
    "/status",
    response_model=Dict[str, Any],
    summary="Server status",
    description="Simple endpoint to verify the server is running.",
)
def check_status() -> Dict[str, Any]:
    """Check server status"""
    return {"status": "success", "message": "Serial connection check."}


@router.post(
    "/api/arduino/send",
    response_model=Dict[str, Any],
    summary="Send command to Arduino",
    description="Forward a raw command string to the connected Arduino.",
)
def send_command(data: Dict[str, Any]) -> Dict[str, Any]:
    """Send command to Arduino"""
    if "command" not in data:
        raise HTTPException(
            status_code=400, detail="Invalid request. 'command' is required."
        )
    try:
        result = als.send_command(data["command"])
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/echo",
    response_model=Dict[str, Any],
    summary="Echo helper",
    description="Return the JSON payload sent in the request body.",
)
def echo(data: Dict[str, Any]) -> Dict[str, Any]:
    """Echo back received data"""
    return {"received": data}
