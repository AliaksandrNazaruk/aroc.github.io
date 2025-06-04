# routes/api/xarm.py

from fastapi import APIRouter, HTTPException
from typing import Dict, Any
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
        return result['result']
    except Exception as e:
        return {"message": str(e)}

@router.post("/command")
async def execute_xarm_command(data: Dict[str, Any]):
    """Execute XArm command"""
    try:
        # Try to acquire the lock with a timeout
        if not await asyncio.wait_for(command_lock.acquire(), timeout=0.1):
            raise HTTPException(
                status_code=409,
                detail="Manipulator is busy with another command"
            )
            
        try:
            loop = asyncio.get_running_loop()
            # Add timeout for command execution
            result = await asyncio.wait_for(
                loop.run_in_executor(None, xarm_command_operator, data),
                timeout=COMMAND_TIMEOUT
            )
            
            if isinstance(result, Exception):
                raise HTTPException(
                    status_code=400,
                    detail=f'XARM Operator: {type(result).__name__}: {result}'
                )
            return result
            
        except asyncio.TimeoutError:
            raise HTTPException(
                status_code=408,
                detail="Command execution timed out"
            )
        finally:
            command_lock.release()
            
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=str(e))
        
