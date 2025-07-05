# services/robot_lib.py
import aiohttp
from typing import Any, Dict, Optional,List,Union
from core.logger import server_logger
from core.connection_config import web_server_ip, web_server_port
from models.api_types import IgusMoveParams,XarmJointsPositionResponse,XarmStatusResponse,ErrorStatus,IgusStatusResponse

class XarmClient:
    def __init__(self, base_url: str | None = None):
        if base_url is None:
            self.base_url = f"http://{web_server_ip}:{web_server_port}/api/v1/xarm"
        self._session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        self._session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._session:
            await self._session.close()
            self._session = None

    async def _post(self, endpoint: str, json: dict) -> Optional[dict]:
        url = f"{self.base_url}{endpoint}"
        try:
            async with self._session.post(url, json=json) as resp:
                data = await resp.json()
                if data:
                    return data
                else:
                    raise Exception(f"Server error")
        except Exception as e:
            server_logger.log_event("error", f"HTTP POST Exception: {e}")
            return None

    async def _get(self, endpoint: str, params: dict = None) -> Optional[dict]:
        url = f"{self.base_url}{endpoint}"
        try:
            async with self._session.get(url, params=params) as resp:
                return await resp.json()
        except Exception as e:
            server_logger.log_event("error", f"HTTP GET Exception: {e}")
            return None

    # Универсальный вызов команды
    async def execute_command(self, command: str, **params) -> Optional[dict]:
        return await self._post("/manipulator/command", {"command": command, **params})

    # --- Методы для новых эндпоинтов ---

    async def get_status(self)-> Union[XarmStatusResponse, ErrorStatus]:
        try:
            result = await self._get("/manipulator/status")
            return XarmStatusResponse(**result)
        except:
            return ErrorStatus(**result)
    
    async def get_current_position(self) -> XarmJointsPositionResponse:
        return await self._get("/manipulator/current_position")
    
    async def get_joints_position(self) -> Optional[dict]:
        return await self._get("/manipulator/joints_position")

    async def take(self) -> Optional[dict]:
        return await self._post("/manipulator/take", {})

    async def drop(self) -> Optional[dict]:
        return await self._post("/manipulator/drop", {})

    async def complex_move_with_joints_dict(self, points: List[dict], velocity: float = 50, blocking: bool = True, reset_faults: bool = False) -> Optional[dict]:
        payload = {
            "points": points,
            "velocity": velocity,
            "blocking": blocking,
            "reset_faults": reset_faults
        }
        return await self._post("/manipulator/complex_move/with_joints_dict", payload)

    async def move_with_joints(self, joints: dict, velocity: float = 50, blocking: bool = True, reset_faults: bool = False) -> Optional[dict]:
        payload = {**joints, "velocity": velocity, "blocking": blocking, "reset_faults": reset_faults}
        return await self._post("/manipulator/move/change_joints", payload)

    async def move_to_pose(self, pose_name: str, velocity: float = 50, blocking: bool = True, reset_faults: bool = False) -> Optional[dict]:
        payload = {"pose_name": pose_name, "velocity": velocity, "blocking": blocking, "reset_faults": reset_faults}
        return await self._post("/manipulator/move/change_pose", payload)

    async def move_tool_position(self, x_offset: float, y_offset: float, z_offset: float, velocity: float = 50, blocking: bool = True, reset_faults: bool = False) -> Optional[dict]:
        payload = {
            "x_offset": x_offset, "y_offset": y_offset, "z_offset": z_offset,
            "velocity": velocity, "blocking": blocking, "reset_faults": reset_faults
        }
        return await self._post("/manipulator/move/change_tool_position", payload)

    async def get_task_status(self, task_id: str) -> Optional[dict]:
        return await self._get("/manipulator/task_status/" + task_id)

    async def joystick_control(self, payload) -> bool:
        return await self._post("/joystick", payload)
        

class IgusClient:
    """
    Async client for the Igus Motor API (FastAPI).
    """

    def __init__(self, base_url: Optional[str] = None):
        if base_url is None:
            base_url = f"http://{web_server_ip}:{web_server_port}/api/v1/igus/motor"
        self.base_url = base_url.rstrip("/")
        self._session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        self._session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._session:
            await self._session.close()

    async def _post(self, endpoint: str, json: dict) -> Optional[dict]:
        url = f"{self.base_url}{endpoint}"
        try:
            async with self._session.post(url, json=json) as resp:
                data = await resp.json()
                if data:
                    return data
                else:
                    raise Exception(f"Server error")
        except Exception as e:
            server_logger.log_event("error", f"HTTP POST Exception: {e}")
            return None

    async def _get(self, endpoint: str, params: dict = None) -> Optional[dict]:
        url = f"{self.base_url}{endpoint}"
        try:
            async with self._session.get(url, params=params) as resp:
                return await resp.json()
        except Exception as e:
            server_logger.log_event("error", f"HTTP GET Exception: {e}")
            return None
        
    async def move_to_position(
        self,
        params: IgusMoveParams
    ) -> Dict[str, Any]:
        """
        Move motor to absolute position. Returns immediate result or task_id for async mode.
        """
        url = f"{self.base_url}/move"
        async with self._session.post(url, json=params) as resp:
            data = await resp.json()
            if resp.status != 200:
                raise Exception(f"Move error: {data}")
            return data

    async def reference(self, blocking: bool = True) -> Dict[str, Any]:
        """
        Start homing/reference procedure.
        """
        url = f"{self.base_url}/reference"
        params = {"blocking": blocking}
        async with self._session.post(url, params=params) as resp:
            data = await resp.json()
            if resp.status != 200:
                raise Exception(f"Reference error: {data}")
            return data

    async def fault_reset(self, blocking: bool = True) -> Dict[str, Any]:
        """
        Reset motor errors.
        """
        url = f"{self.base_url}/fault_reset"
        params = {"blocking": blocking}
        async with self._session.post(url, params=params) as resp:
            data = await resp.json()
            if resp.status != 200:
                raise Exception(f"Fault reset error: {data}")
            return data

    async def get_status(self) -> Dict[str, Any]:
        try:
            result = await self._get("/status")
            return IgusStatusResponse(**result)
        except:
            return ErrorStatus(**result)
        url = f"{self.base_url}/status"
        async with self._session.get(url) as resp:
            data = await resp.json()
            if resp.status != 200:
                raise Exception(f"Status error: {data}")
            return data

    async def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """
        Get status/result for an async task.
        """
        url = f"{self.base_url}/task_status/{task_id}"
        async with self._session.get(url) as resp:
            data = await resp.json()
            if resp.status != 200:
                raise Exception(f"Task status error: {data}")
            return data
        

    async def healthcheck(self) -> bool:
        """
        Simple health check.
        """
        url = f"{self.base_url}/health"
        async with self._session.get(url) as resp:
            data = await resp.json()
            return data.get("status") == "ok"
