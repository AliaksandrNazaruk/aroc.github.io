import asyncio
from typing import Callable
from core.state import igus_manager

motor_lock = asyncio.Lock()

async def guarded_motor_command(func: Callable, *args, **kwargs):
    if motor_lock.locked():
        raise RuntimeError("Motor is busy")
    async with motor_lock:
        return await _execute_motor_command(func, *args, **kwargs)

async def _execute_motor_command(func: Callable, *args, **kwargs):
    loop = asyncio.get_event_loop()
    try:
        result = await loop.run_in_executor(None, lambda: func(*args, **kwargs))
        if hasattr(result, "result") and hasattr(result, "done"):
            result = result.result(timeout=10)
        return result
    except Exception as e:
        raise RuntimeError(f"{func.__name__} failed: {e}")

async def move_motor_command( position, velocity, acceleration, blocking=True):
    return await guarded_motor_command(
        igus_manager.move_to_position,
        target_position=position*1000,
        velocity=velocity*100,
        acceleration=acceleration*100,
        blocking=blocking,
    )

async def reference_motor_command():
    return await guarded_motor_command(igus_manager.home)

async def reset_faults_command():
    return await guarded_motor_command(igus_manager.fault_reset)

def get_motor_position_command():
    result = igus_manager.get_position()
    return float(result["position"]/1000)

def get_motor_motion_command():
    result = igus_manager.get_is_motion()
    return result["is_motion"]

async def get_motor_status_command():
    result = await _execute_motor_command(igus_manager.get_status)
    return {
        "status_word": result["statusword"],
        "homed": result["homed"],
        "error": result["error_state"],
        "connected": result["connected"],
        "position_cm": float(result["position"]/1000)
    }
