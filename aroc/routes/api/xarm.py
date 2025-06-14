# routes/api/xarm.py

from fastapi import APIRouter, HTTPException
from typing import Dict, Any

from core.logger import server_logger
from drivers.xarm_scripts.xarm_command_operator import xarm_command_operator
import asyncio
from asyncio import Lock
from contextlib import asynccontextmanager

router = APIRouter(prefix="/api/xarm", tags=["xarm"])

# Use a Lock instead of a global variable
command_lock = Lock()
# Timeout for command execution (in seconds)
COMMAND_TIMEOUT = 30

@router.get("/data")
async def get_xarm_data():
    """Get current XArm state"""
    server_logger.log_event("info", "GET /api/xarm/data")
    data = {
        "command": "get_data",
        "depth": 0
    }
    try:
        # Check if the manipulator is busy
        if command_lock.locked():
            return {"message": "manipulator is busy"}
            
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(None, xarm_command_operator, data)

        if not result.get("success"):
            server_logger.log_event("error", result.get("error", "unknown error"))
            return {"message": result.get("error", "unknown error")}

        server_logger.log_event("info", "XArm data fetched")
        return result["result"]
    except Exception as e:
        server_logger.log_event("error", f"get_xarm_data failed: {e}")
        return {"message": str(e)}

@router.post("/command")
async def execute_xarm_command(data: Dict[str, Any]):
    """Execute XArm command"""
    server_logger.log_event("info", f"POST /api/xarm/command {data}")

    lock_acquired = False
    try:
        try:
            await asyncio.wait_for(command_lock.acquire(), timeout=0.1)
            lock_acquired = True
        except asyncio.TimeoutError:
            raise HTTPException(
                status_code=409,
                detail="Manipulator is busy with another command",
            )

        try:
            loop = asyncio.get_running_loop()
            # Add timeout for command execution
            result = await asyncio.wait_for(
                loop.run_in_executor(None, xarm_command_operator, data),
                timeout=COMMAND_TIMEOUT,
            )

            if isinstance(result, Exception):
                raise HTTPException(
                    status_code=400,
                    detail=f"XARM Operator: {type(result).__name__}: {result}",
                )

            if not result.get("success"):
                raise HTTPException(
                    status_code=result.get("error_code", 400),
                    detail=result.get("error", "Unknown error"),
                )

            server_logger.log_event("info", "XArm command executed")
            return result["result"]

        except asyncio.TimeoutError:
            server_logger.log_event("error", "XArm command timeout")
            raise HTTPException(
                status_code=408,
                detail="Command execution timed out",
            )
        finally:
            if lock_acquired:
                command_lock.release()

    except Exception as e:
        server_logger.log_event("error", f"execute_xarm_command failed: {e}")
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=str(e))
