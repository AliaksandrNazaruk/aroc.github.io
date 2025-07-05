from typing import Optional
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Union

# --------- КООРДИНАТЫ И ОФФСЕТЫ ---------
class ProductLocation(BaseModel):
    """Target location on AGV map (all units in mm/rad)."""
    x_mm: float = Field(..., description="X coordinate in millimeters", example=0.0)
    y_mm: float = Field(..., description="Y coordinate in millimeters", example=0.0)
    theta_rad: float = Field(0.0, description="Orientation (radians)", example=0.0)
    map_id: Optional[str] = Field(None, description="AGV map identifier", example="factory_map")

class XarmToolOffsets(BaseModel):
    """Offsets for xArm tool (all in mm)."""
    x_offset_mm: float = Field(..., ge=-1000, le=1000, description="Tool X offset in mm", example=0)
    y_offset_mm: float = Field(..., ge=-1000, le=1000, description="Tool Y offset in mm", example=0)
    z_offset_mm: float = Field(..., ge=-1000, le=1000, description="Tool Z offset in mm", example=0)

# --------- REQUESTS ---------
class DefaultMoveRequest(BaseModel):
    """Minimal request for movement (velocity only)."""
    velocity_percent: float = Field(..., ge=1, le=100, description="Speed (%)", example=20)
    blocking: bool = Field(True, description="Wait for completion", example=True)

class RobotMoveRequest(BaseModel):
    """Coordinated movement request."""
    product_id: str = Field(..., description="Product identifier", example="PRODUCT_1")
    location: ProductLocation = Field(..., description="Target location")
    lift_position_mm: Optional[float] = Field(None, description="Igus lift position (mm)", example=30)
    manipulator_offsets: Optional[XarmToolOffsets] = Field(None, description="xArm tool offsets (mm)")
    velocity_percent: float = Field(..., ge=1, le=100, description="Speed (%)", example=20)
    reset_faults: bool = Field(False, description="Reset errors and reinitialize before move", example=False)
    blocking: bool = Field(True, description="Wait for completion", example=True)

# --------- ОТВЕТЫ НА ДВИЖЕНИЕ ---------
class SymovoMoveResult(BaseModel):
    success: bool = Field(..., description="True if AGV movement succeeded")
    position_mm: Optional[float] = Field(None, description="Final AGV position (mm)")
    details: Optional[str] = Field(None, description="Movement details or message")
    error: Optional[str] = Field(None, description="Error message, if any")

class IgusMoveResult(BaseModel):
    success: bool = Field(..., description="True if Igus lift movement succeeded")
    position_mm: Optional[float] = Field(None, description="Final lift position (mm)")
    details: Optional[str] = Field(None, description="Movement details or message")
    error: Optional[str] = Field(None, description="Error message, if any")

class XarmMoveResult(BaseModel):
    success: bool = Field(..., description="True if manipulator movement succeeded")
    details: Optional[str] = Field(None, description="Movement details or message")
    error: Optional[str] = Field(None, description="Error message, if any")

# --------- КООРДИНИРОВАННЫЕ ОТВЕТЫ ---------
class RobotMoveResult(BaseModel):
    success: bool = Field(..., description="True if move was executed successfully")
    agv_result: Optional[SymovoMoveResult] = Field(None, description="AGV movement result")
    lift_result: Optional[IgusMoveResult] = Field(None, description="Igus lift movement result")
    manipulator_result: Optional[XarmMoveResult] = Field(None, description="xArm manipulator movement result")
    message: Optional[str] = Field(None, description="General error or info message")

class RobotMoveBoxResult(BaseModel):
    success: bool = Field(..., description="True if the robot placed product in Box 1")
    igus_result: Optional[IgusMoveResult] = Field(None, description="Igus lift movement details")
    manipulator_result: Optional[XarmMoveResult] = Field(None, description="xArm manipulator movement details")
    message: Optional[str] = Field(None, description="Additional information or error message")

class RobotTransportPositionResult(BaseModel):
    success: bool = Field(..., description="True if robot moved to transport (stowed) position")
    igus_result: Optional[IgusMoveResult] = Field(None, description="Igus lift first move details")
    igus_final_result: Optional[IgusMoveResult] = Field(None, description="Igus lift final move details")
    manipulator_result: Optional[XarmMoveResult] = Field(None, description="xArm manipulator movement details")
    message: Optional[str] = Field(None, description="Additional information or error message")

# --------- СТАТУСЫ ПОДСИСТЕМ ---------

class ErrorStatus(BaseModel):
    error: dict

class IgusStatusResponse(BaseModel):
    """Current status of the motor controller."""
    status_word: int = Field(..., description="Status word from the motor controller", example=8192)
    homed: bool = Field(..., description="True if the motor is homed", example=True)
    error: bool = Field(..., description="True if there is an error", example=False)
    connected: bool = Field(..., description="True if the motor is connected", example=True)
    position_cm: float = Field(
        0.0, ge=0.0, le=120.0,
        description="Current position in centimeters (0.00–120.00)", example=50.0
    )

class TaskStatusResponse(BaseModel):
    """Information about an asynchronous motor task."""
    status: str = Field(..., description="Current task status, e.g. 'working', 'finished', 'error'", example="working")
    result: Optional[Any] = Field(None, description="Result returned when the task completes, if any")

class IgusMoveParams(BaseModel):
    """Parameters for a single motor move command."""
    position_cm: float = Field(
        0.0,
        ge=0.0, le=120.0,
        description="Target position in centimeters (0.00–120.00)", example=50.0
    )
    velocity_percent: float = Field(
        0.0,
        ge=0.0, le=100.0,
        description="Movement velocity as percent (1–100)", example=50.0
    )
    acceleration_percent: float = Field(
        0.0,
        ge=0.0, le=100.0,
        description="Movement acceleration as percent (1–100)", example=50.0
    )
    blocking: bool = Field(
        True,
        description="If True, wait until move completes before returning response", example=True
    )

class IgusCommandResponse(BaseModel):
    """Response for any synchronous motor command."""
    success: bool = Field(..., description="True if the command was successful", example=True)

class IgusAsyncResponse(BaseModel):
    """Response for an async motor command (task)."""
    success: bool = Field(..., description="True if the task was started successfully", example=True)
    task_id: str = Field(..., description="Task identifier (UUID)", example="123e4567-e89b-12d3-a456-426614174000")

class IgusPositionResponse(BaseModel):
    """Only current position of the motor."""
    position_cm: float = Field(
        0.0, ge=0.0, le=120.0,
        description="Current position in centimeters (0.00–120.00)", example=50.0
    )

class IgusMotionResponse(BaseModel):
    """Current motion state of the motor."""
    is_moving: bool = Field(
        ..., description="True if the motor is currently moving", example=False
    )
# --- AGV Геометрия и скорость ---

class SymovoPose(BaseModel):
    """Pose of the AGV on the map."""
    x_m: float = Field(..., description="X coordinate in meters", example=0.0)
    y_m: float = Field(..., description="Y coordinate in meters", example=0.0)
    theta_rad: float = Field(..., description="Orientation angle in radians", example=0.0)
    map_id: Optional[str] = Field(None, description="Map identifier", example="warehouse")

class SymovoVelocity(BaseModel):
    """Current AGV velocity components."""
    vx_m_s: float = Field(..., description="Linear velocity X (m/s)", example=0.0)
    vy_m_s: float = Field(..., description="Linear velocity Y (m/s)", example=0.0)
    omega_rad_s: float = Field(..., description="Angular velocity (rad/s)", example=0.0)
# --- AGV Состояние и статусы ---

class SymovoStatusResponse(BaseModel):
    """Current status of the Symovo AGV."""
    online: bool = Field(..., description="True if AGV is online", example=True)
    last_update_time: Optional[str] = Field(None, description="Timestamp of last status update (ISO 8601)", example="2024-01-01T12:00:00Z")
    id: Optional[str] = Field(None, description="AGV identifier", example="agv01")
    name: Optional[str] = Field(None, description="AGV display name", example="AGV 1")
    pose: SymovoPose = Field(..., description="Current AGV pose on map")
    velocity: SymovoVelocity = Field(..., description="Current AGV velocity")
    state: Optional[str] = Field(None, description="Current AGV state", example="IDLE")
    battery_level_percent: Optional[float] = Field(None, description="Battery level (%)", example=90.0)
    state_flags: Optional[Any] = Field(None, description="Internal state flags (object/bitfield)")
    robot_ip: Optional[str] = Field(None, description="AGV IP address", example="192.168.1.100")
    replication_port: Optional[int] = Field(None, description="Replication TCP port", example=8004)
    api_port: Optional[int] = Field(None, description="REST API TCP port", example=8004)
    iot_port: Optional[int] = Field(None, description="IoT/MQTT port", example=9000)
    last_seen: Optional[str] = Field(None, description="Last time AGV responded (ISO 8601)", example="2024-01-01T12:00:01Z")
    enabled: Optional[bool] = Field(None, description="True if AGV is enabled for operation", example=True)
    last_update_epoch: Optional[float] = Field(None, description="Last update time (epoch)", example=1710000000.0)
    attributes: Optional[Any] = Field(None, description="Additional attributes (object, optional)")
    planned_path_edges: Optional[Any] = Field(None, description="Currently planned path edges (object/list, optional)")
# --- Статус и результат универсальных команд ---

class NewJobResponse(BaseModel):
    """Response after starting a new AGV job."""
    status: str = Field(..., description="Job operation status", example="ok")
    message: str = Field(..., description="Human-readable status message", example="Job started")
    result: Any = Field(..., description="Job result object (varies by job type)")

class GenericResult(BaseModel):
    """General result wrapper."""
    status: str = Field(..., description="Operation status", example="ok")
    result: Any = Field(..., description="Result object or value")
# --- Команды движения AGV ---

class MoveToPoseRequest(BaseModel):
    """Request parameters for commanding AGV to a pose."""
    x_m: float = Field(..., description="Target X position in meters", example=1.0)
    y_m: float = Field(..., description="Target Y position in meters", example=2.0)
    theta_rad: float = Field(0.0, description="Target orientation in radians", example=0.0)
    map_id: Optional[str] = Field(None, description="Target map identifier", example="warehouse")
    max_speed_m_s: Optional[float] = Field(None, description="Maximum speed (m/s)", example=0.5)

class XarmJointsDict(BaseModel):
    """Single set of xArm joint positions, degrees."""
    j1_deg: float = Field(..., description="Joint 1 angle (degrees)", example=0.0)
    j2_deg: float = Field(..., description="Joint 2 angle (degrees)", example=0.0)
    j3_deg: float = Field(..., description="Joint 3 angle (degrees)", example=0.0)
    j4_deg: float = Field(..., description="Joint 4 angle (degrees)", example=0.0)
    j5_deg: float = Field(..., description="Joint 5 angle (degrees)", example=0.0)
    j6_deg: float = Field(..., description="Joint 6 angle (degrees)", example=0.0)


class XarmMoveWithToolParams(BaseModel):
    """Move manipulator by tool offsets."""
    x_offset_mm: float = Field(..., ge=-1000, le=1000, description="Tool X offset (mm)", example=0.0)
    y_offset_mm: float = Field(..., ge=-1000, le=1000, description="Tool Y offset (mm)", example=0.0)
    z_offset_mm: float = Field(..., ge=-1000, le=1000, description="Tool Z offset (mm)", example=0.0)
    velocity_percent: float = Field(..., ge=0, le=100, description="Manipulator speed (%)", example=50.0)
    reset_faults: bool = Field(False, description="Reset errors and reinitialize before move", example=False)
    blocking: bool = Field(True, description="Wait for move completion", example=True)

class XarmMoveWithPoseParams(BaseModel):
    """Move manipulator to a named pose."""
    pose_name: str = Field(..., description="Target pose name", example="READY_SECTION_CENTER")
    velocity_percent: float = Field(..., ge=0, le=100, description="Manipulator speed (%)", example=50.0)
    reset_faults: bool = Field(False, description="Reset errors and reinitialize before move", example=False)
    blocking: bool = Field(True, description="Wait for move completion", example=True)

class XarmMoveWithJointsParams(BaseModel):
    """Move manipulator to specific joint angles."""
    j1_deg: float = Field(..., ge=-500, le=500, description="Joint 1 angle (degrees)", example=0.0)
    j2_deg: float = Field(..., ge=-500, le=500, description="Joint 2 angle (degrees)", example=0.0)
    j3_deg: float = Field(..., ge=-500, le=500, description="Joint 3 angle (degrees)", example=0.0)
    j4_deg: float = Field(..., ge=-500, le=500, description="Joint 4 angle (degrees)", example=0.0)
    j5_deg: float = Field(..., ge=-500, le=500, description="Joint 5 angle (degrees)", example=0.0)
    j6_deg: float = Field(..., ge=-500, le=500, description="Joint 6 angle (degrees)", example=0.0)
    velocity_percent: float = Field(..., ge=0, le=100, description="Manipulator speed (%)", example=50.0)
    reset_faults: bool = Field(False, description="Reset errors and reinitialize before move", example=False)
    blocking: bool = Field(True, description="Wait for move completion", example=True)

class XarmPositionResponse(BaseModel):
    pose_name: str = Field(..., description="", example="Test name")
    points: XarmJointsDict = Field(
        ...,
        description="List of joints positions, each as a dict with keys 'j1'..'j6'",
        example={"j1": 0, "j2": 10, "j3": 20, "j4": 30, "j5": 40, "j6": 50}
    )
    
class XarmMoveWithJointsDictParams(BaseModel):
    """Move manipulator along a sequence of joint positions."""
    points: List[XarmJointsDict] = Field(
        ..., description="List of joint positions, each with keys 'j1_deg'..'j6_deg'",
        example=[
            {"j1_deg": 0, "j2_deg": 10, "j3_deg": 20, "j4_deg": 30, "j5_deg": 40, "j6_deg": 50},
            {"j1_deg": 10, "j2_deg": 20, "j3_deg": 30, "j4_deg": 40, "j5_deg": 50, "j6_deg": 60},
        ]
    )
    velocity_percent: float = Field(..., ge=0, le=100, description="Manipulator speed (%)", example=50.0)
    reset_faults: bool = Field(False, description="Reset errors and reinitialize before move", example=False)
    blocking: bool = Field(True, description="Wait for move completion", example=True)

class XarmCommandResponse(BaseModel):
    """Response for synchronous manipulator commands."""
    success: bool = Field(..., description="True if command completed successfully", example=True)

class XarmAsyncResponse(BaseModel):
    """Response for async manipulator commands."""
    success: bool = Field(..., description="True if command started successfully", example=True)
    task_id: str = Field(..., description="Async task identifier (UUID)", example="123e4567-e89b-12d3-a456-426614174000")

class XarmStatusResponse(BaseModel):
    """Full status of the manipulator controller."""
    alive: bool = Field(..., description="Controller heartbeat flag", example=True)
    connected: bool = Field(..., description="True if xArm is connected", example=False)
    state_code: int = Field(..., description="Internal controller state code", example=0)
    has_err_warn: bool = Field(..., description="True if warnings or errors present", example=True)
    has_error: bool = Field(..., description="True if an error is active", example=False)
    has_warn: bool = Field(..., description="True if warnings are present", example=True)
    error_code: int = Field(..., description="Current error code (0 means no error)", example=0)

class XarmJointsPositionResponse(BaseModel):
    """Current joint angles reported by the manipulator."""
    joints_deg: Dict[str, float] = Field(
        ..., description="Current joint angles in degrees. Keys: j1_deg..j6_deg",
        example={"j1_deg": 0, "j2_deg": 0, "j3_deg": 0, "j4_deg": 0, "j5_deg": 0, "j6_deg": 0}
    )

class RobotSystemStatus(BaseModel):
    ready: bool = Field(..., description="True if all subsystems are ready for operation")
    message: str = Field(..., description="If not ready, explanation; empty if ready")
    xarm: Union[XarmStatusResponse, ErrorStatus]
    igus: Union[IgusStatusResponse, ErrorStatus]
    symovo: Union[SymovoStatusResponse, ErrorStatus]
