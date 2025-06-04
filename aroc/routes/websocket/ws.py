# routes/websocket/ws.py

from fastapi import APIRouter, WebSocket
from utils.ws_proxy import proxy_websocket

router = APIRouter(tags=["websockets"])

@router.websocket("/depth")
async def depth_ws(websocket: WebSocket):
    """WebSocket proxy for depth camera"""
    await proxy_websocket(websocket, "ws://192.168.1.55:9999")

@router.websocket("/depth_query")
async def depth_query_ws(websocket: WebSocket):
    """WebSocket proxy for depth query camera"""
    await proxy_websocket(websocket, "ws://192.168.1.55:10000")

@router.websocket("/color")
async def color_ws(websocket: WebSocket):
    """WebSocket proxy for color camera"""
    await proxy_websocket(websocket, "ws://192.168.1.55:9998")

@router.websocket("/camera2")
async def camera2_ws(websocket: WebSocket):
    """WebSocket proxy for second camera"""
    await proxy_websocket(websocket, "ws://localhost:9998")

@router.websocket("/igus")
async def igus_ws(websocket: WebSocket):
    """WebSocket proxy for Igus motor"""
    await proxy_websocket(websocket, "ws://localhost:8020")
