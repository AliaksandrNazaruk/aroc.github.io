from fastapi.responses import FileResponse, JSONResponse
from typing import Dict, Any
import os
from fastapi import APIRouter, HTTPException, status
from db.trajectory import get_trajectory, save_trajectory

import arduino_controller.arduino_led_controller as als

router = APIRouter(tags=["misc"])

@router.get("/")
def get_root():
    """Serve index.html"""
    filename = "index.html"
    if not os.path.exists(filename):
        return JSONResponse(content={"error": "File not found"}, status_code=404)
    return FileResponse(filename)

@router.get("/control")
def get_control_page():
    """Serve control page"""
    filename = "index.html"
    if not os.path.exists(filename):
        return JSONResponse(content={"error": "File not found"}, status_code=404)
    return FileResponse(filename)
# routes/trajectory.py

@router.get("/api/trajectory")
def api_get_trajectory():
    config = get_trajectory()
    if config is None:
        raise HTTPException(status_code=404, detail="Trajectory configuration not found.")
    return config

@router.post("/api/trajectory", status_code=status.HTTP_201_CREATED)
def api_save_trajectory(config: dict):
    try:
        save_trajectory(config)
        return {"status": "ok", "message": "Trajectory configuration saved."}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/status")
def check_status():
    """Check server status"""
    return {"status": "success", "message": "Serial connection check."}

@router.post("/api/arduino/send")
def send_command(data: Dict[str, Any]):
    """Send command to Arduino"""
    if "command" not in data:
        raise HTTPException(status_code=400, detail="Invalid request. 'command' is required.")
    try:
        result = als.send_command(data["command"])
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/echo")
def echo(data: Dict[str, Any]):
    """Echo back received data"""
    return {"received": data}
