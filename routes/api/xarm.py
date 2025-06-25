
from drivers.xarm_scripts.xarm_command_operator import xarm_command_operator
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from fastapi.concurrency import run_in_threadpool
from typing import Any, Callable, Dict, Optional

from core.logger import server_logger

router = APIRouter(prefix="/api/v1/xarm", tags=["Xarm Manipulator"])

class XarmMoveParams(BaseModel):
    position: int = Field(..., description="Target position in encoder units")
    velocity: int = Field(5000, description="Motion velocity")
    acceleration: int = Field(5000, description="Motion acceleration")
    wait: bool = Field(True, description="Wait until move complete")

class XarmCommandResponse(BaseModel):
    success: bool
    result: Optional[Dict[str, Any]]
    error: Optional[str]
    state: Dict[str, Any]

class XarmStatusResponse(BaseModel):
    success: bool = Field(..., description="Was request successful")
    result: Optional[Dict[str, Any]] = Field(None, description="Manipulator status data")
    error: Optional[str] = Field(None, description="Error message, if any")
    error_code: Optional[int] = Field(None, description="Error code, if any")

@router.get(
    "/manipulator/status",
    response_model=XarmStatusResponse,
    status_code=200,
    summary="Get Xarm manipulator status",
    description="Returns the current status and error state of the Xarm manipulator.",
    response_model_exclude_unset=True,
)
async def get_xarm_status():
    try:
        _result = await xarm_command_operator({"command": "get_data","depth": 0})
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Failed to get motor status: {str(e)}"
        )
    return XarmStatusResponse(
        success=_result.get("success"),
        result=_result.get("result"),
        error=_result.get("error"),
        error_code=_result.get("error_code"),
    )

# async def execute_xarm_command(func: Callable, *args, **kwargs) -> Dict[str, Any]:
#     """Run a blocking xarm command in a threadpool and build a response."""
#     try:
#         result = await run_in_threadpool(func, *args, **kwargs)
#         return _build_response(True, result=result)
#     except Exception as e:
#         server_logger.log_event("error", f"{func.__name__} failed: {e}")
#         return _build_response(False, error=str(e))
    
# @router.post(
#     "/motor/command",
#     response_model=XarmCommandResponse,
#     status_code=200,
#     summary="Moving xarm commands",
#     description=""
# )
# async def execute_xarm_command(data: Dict[str, Any]):
#     try:
#         response = await execute_xarm_command(
#             igus_motor.move_to_position,
#             target_position=params.position,
#             velocity=params.velocity,
#             acceleration=params.acceleration,
#             blocking=params.wait,
#         )
#         response["result"] = {"position": igus_motor._position}
#         if not response["success"]:
#             raise HTTPException(
#                 status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
#                 detail=response["error"] or "Unknown motor error"
#             )
#         return response
#     except Exception as e:
#         raise HTTPException(
#             status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
#             detail=f"Motor move failed: {str(e)}"
#         )



@router.get("/health", summary="Check API health", description="Healthcheck endpoint")
async def healthcheck():
    return {"status": "ok"}
