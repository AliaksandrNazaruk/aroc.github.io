# routes/websocket/ws.py

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import asyncio
from typing import Dict
import time
from utils.ws_proxy import proxy_websocket
from core.logger import server_logger
from core.state import virtual_joysticks
from core.connection_config import (
    camera_depth_ws_url,
    camera_depth_query_ws_url,
    camera_color_ws_url,
    camera2_ws_url,
    igus_ws_url,
)

router = APIRouter(tags=["websockets"])

@router.websocket("/depth")
async def depth_ws(websocket: WebSocket):
    """WebSocket proxy for depth camera"""
    server_logger.log_event("debug", "WS /depth connected")
    await proxy_websocket(websocket, camera_depth_ws_url)
    server_logger.log_event("error", "WS /depth disconnected")

@router.websocket("/depth_query")
async def depth_query_ws(websocket: WebSocket):
    """WebSocket proxy for depth query camera"""
    server_logger.log_event("debug", "WS /depth_query connected")
    await proxy_websocket(websocket, camera_depth_query_ws_url)
    server_logger.log_event("error", "WS /depth_query disconnected")

@router.websocket("/color")
async def color_ws(websocket: WebSocket):
    """WebSocket proxy for color camera"""
    server_logger.log_event("debug", "WS /color connected")
    await proxy_websocket(websocket, camera_color_ws_url)
    server_logger.log_event("error", "WS /color disconnected")

@router.websocket("/camera2")
async def camera2_ws(websocket: WebSocket):
    """WebSocket proxy for second camera"""
    server_logger.log_event("debug", "WS /camera2 connected")
    await proxy_websocket(websocket, camera2_ws_url)
    server_logger.log_event("error", "WS /camera2 disconnected")

@router.websocket("/igus")
async def igus_ws(websocket: WebSocket):
    """WebSocket proxy for Igus motor"""
    server_logger.log_event("debug", "WS /igus connected")
    await proxy_websocket(websocket, igus_ws_url)
    server_logger.log_event("error", "WS /igus disconnected")

BUTTON_TIMEOUT = 0.2

@router.websocket("/joystick")
async def joystick_ws(websocket: WebSocket):
    await websocket.accept()
    joystick_id = str(id(websocket))
    virtual_joysticks[joystick_id] = {
        "axes": {},
        "buttons": {},
        "button_timers": {},
        "axis_timers": {},
    }
    try:
        while True:
            data = await websocket.receive_json()
            axes = data.get("axes", {})
            buttons = data.get("buttons", {})

            # Обновляем оси
            for axis, value in axes.items():
                virtual_joysticks[joystick_id]["axes"][axis] = value
                # Перезапускаем таймер сброса оси
                if axis in virtual_joysticks[joystick_id]["axis_timers"]:
                    virtual_joysticks[joystick_id]["axis_timers"][axis].cancel()
                virtual_joysticks[joystick_id]["axis_timers"][axis] = asyncio.create_task(
                    reset_axis_after_timeout(joystick_id, axis, BUTTON_TIMEOUT)
                )

            # Обновляем кнопки
            for btn, state in buttons.items():
                virtual_joysticks[joystick_id]["buttons"][btn] = state
                if btn in virtual_joysticks[joystick_id]["button_timers"]:
                    virtual_joysticks[joystick_id]["button_timers"][btn].cancel()
                virtual_joysticks[joystick_id]["button_timers"][btn] = asyncio.create_task(
                    reset_button_after_timeout(joystick_id, btn, BUTTON_TIMEOUT)
                )
            await websocket.send_json({"status": "ok"})
    except WebSocketDisconnect:
        print(f"Joystick {joystick_id} disconnected")
    finally:
        # Чистим таймеры
        for t in virtual_joysticks[joystick_id]["button_timers"].values():
            t.cancel()
        for t in virtual_joysticks[joystick_id]["axis_timers"].values():
            t.cancel()
        virtual_joysticks.pop(joystick_id, None)

async def update_virtual_joystick(joystick_id, axes, buttons, timeout=0.2):
    js = virtual_joysticks.setdefault(joystick_id, {"axes": {}, "buttons": {}})
    for axis, value in axes.items():
        js["axes"][axis] = value
        # Запускаем таймер сброса на каждую ось
        asyncio.create_task(reset_axis_after_timeout(joystick_id, axis, timeout))
    for btn, value in buttons.items():
        js["buttons"][btn] = value
        if value:  # сбрасываем только если нажата
            asyncio.create_task(reset_button_after_timeout(joystick_id, btn, timeout))

async def reset_axis_after_timeout(joystick_id, axis, timeout):
    await asyncio.sleep(timeout)
    js = virtual_joysticks.get(joystick_id)
    if js:
        js["axes"][axis] = 0.0  # DEADZONE или твой ноль

async def reset_button_after_timeout(joystick_id, btn, timeout):
    await asyncio.sleep(timeout)
    js = virtual_joysticks.get(joystick_id)
    if js:
        js["buttons"][btn] = False

def get_joystick_state(joystick_id: str):
    return virtual_joysticks.get(joystick_id, {})