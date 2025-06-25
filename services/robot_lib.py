# services/robot_lib.py
import aiohttp
import asyncio
from typing import List, Dict, Any
from core.logger import server_logger

from core.connection_config import web_server_ip, web_server_port

class XarmClient:
    def __init__(self, base_url: str | None = None):
        if base_url is None:
            base_url = f"http://{web_server_ip}:{web_server_port}"
        self.base_url = base_url
        self._session = None

    async def __aenter__(self):
        self._session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._session:
            await self._session.close()

    async def execute_command(self, command: str, **params) -> Dict[str, Any | None]:
        try:
            async with self._session.post(f"{self.base_url}/api/xarm/command", json={"command": command, **params}) as response:
                data = await response.json()
                if data['error']:
                    server_logger.log_event("error", f"Server error: {data['error_code']}")
                    raise Exception(f"Server error: {data['error_code']}")
                return data
        except Exception as e:
            server_logger.log_event("error", f"Exception: {e}")
        return None


    async def get_data(self) -> Dict[str, Any]:
        async with self._session.get(f"{self.base_url}/api/xarm/data") as response:
            return await response.json()

    async def take(self,depth=0):
        return await self.execute_command("take", depth=depth)

    async def put(self):
        return await self.execute_command("put")

    async def get_current_position(self):
        try:
            return await self.execute_command("get_current_position")
        except Exception as e:
            server_logger.log_event("error", str(e))


    async def go_to_position(self, positions: List[str], angle_speed=20):
        try:
            result = await self.execute_command(
                "move_to_position",
                positions=positions,
                angle_speed=angle_speed,
            )
            return result
        except Exception as e:
            # The previous implementation attempted to print the exception but
            # omitted the message, effectively swallowing the error.  Log it so
            # that the caller can inspect what went wrong.
            server_logger.log_event("error", str(e))
            return None

    async def move_tool_position(self, x: float, y: float, z: float, angle_speed=20):
        """Move tool by XYZ coordinates relative to the current pose."""
        try:
            result = await self.execute_command(
                "move_tool_position",
                x=x,
                y=y,
                z=z,
                angle_speed=angle_speed,
            )
            return result
        except Exception as e:
            server_logger.log_event("error", str(e))
            return None


import aiohttp
import asyncio
from typing import Dict, Any


class IgusClient:
    def __init__(self, base_url: str | None = None):
        if base_url is None:
            base_url = f"http://{web_server_ip}:{web_server_port}"
        self.base_url = base_url
        self._session: aiohttp.ClientSession | None = None

    async def __aenter__(self):
        self._session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._session:
            await self._session.close()

    async def move_to_position(
        self,
        position: int,
        velocity: int = 50,
        acceleration: int = 50,
        wait: bool = True
    ) -> Dict[str, Any]:
        if velocity>100:velocity=100
        if velocity<0:velocity=1
        if acceleration>100:acceleration=100
        if acceleration<0:acceleration=1
        url = f"{self.base_url}/api/v1/igus/motor/move_to_position"
        payload = {
            "position": position,
            "velocity": velocity*100,
            "acceleration": acceleration*100,
            "wait": wait,
        }
        async with self._session.post(url, json=payload) as response:
            return await response.json()

    async def reference(self) -> Dict[str, Any]:
        url = f"{self.base_url}/api/v1/igus/motor/reference"
        async with self._session.post(url) as response:
            return await response.json()

    async def fault_reset(self) -> Dict[str, Any]:
        url = f"{self.base_url}/api/v1/igus/motor/fault_reset"
        async with self._session.post(url) as response:
            return await response.json()

    async def get_state(self) -> Dict[str, Any]:
        url = f"{self.base_url}/api/v1/igus/motor/status"
        async with self._session.get(url) as response:
            return await response.json()

