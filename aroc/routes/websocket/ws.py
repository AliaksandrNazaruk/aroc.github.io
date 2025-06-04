# routes/websocket/ws.py

from fastapi import APIRouter, WebSocket
from utils.ws_proxy import proxy_websocket
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
    await proxy_websocket(websocket, camera_depth_ws_url)

@router.websocket("/depth_query")
async def depth_query_ws(websocket: WebSocket):
    """WebSocket proxy for depth query camera"""
    await proxy_websocket(websocket, camera_depth_query_ws_url)

@router.websocket("/color")
async def color_ws(websocket: WebSocket):
    """WebSocket proxy for color camera"""
    await proxy_websocket(websocket, camera_color_ws_url)

@router.websocket("/camera2")
async def camera2_ws(websocket: WebSocket):
    """WebSocket proxy for second camera"""
    await proxy_websocket(websocket, camera2_ws_url)

@router.websocket("/igus")
async def igus_ws(websocket: WebSocket):
    """WebSocket proxy for Igus motor"""
    await proxy_websocket(websocket, igus_ws_url)
