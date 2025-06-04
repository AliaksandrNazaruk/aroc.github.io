# services/robot_lib.py
import aiohttp
import asyncio
from typing import List, Dict, Any

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

    async def execute_command(self, command: str, **params) -> Dict[str, Any]:
        async with self._session.post(f"{self.base_url}/api/xarm/command", json={"command": command, **params}) as response:
            return await response.json()

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
            print(e)


    async def go_to_position(self, positions: List[str], angle_speed=20):
        try:
            return await self.execute_command(
                "move_to_position",
                positions=positions,
                angle_speed=angle_speed,
            )
        except Exception as e:
            # The previous implementation attempted to print the exception but
            # omitted the message, effectively swallowing the error.  Log it so
            # that the caller can inspect what went wrong.
            print(e)
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
        velocity: int = 5000,
        acceleration: int = 5000,
        wait: bool = True
    ) -> Dict[str, Any]:
        url = f"{self.base_url}/api/igus/move_to_position"
        payload = {
            "position": position,
            "velocity": velocity,
            "acceleration": acceleration,
            "wait": wait,
        }
        async with self._session.post(url, json=payload) as response:
            return await response.json()

    async def reference(self) -> Dict[str, Any]:
        url = f"{self.base_url}/api/igus/reference"
        async with self._session.post(url) as response:
            return await response.json()

    async def fault_reset(self) -> Dict[str, Any]:
        url = f"{self.base_url}/api/igus/fault_reset"
        async with self._session.post(url) as response:
            return await response.json()

    async def get_state(self) -> Dict[str, Any]:
        url = f"{self.base_url}/api/igus/state"
        async with self._session.get(url) as response:
            return await response.json()
