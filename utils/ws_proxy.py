from fastapi import WebSocket
import websockets
from typing import Optional
import asyncio

async def forward_messages_fastapi_to_websockets(src_ws: WebSocket, dst_ws: websockets.WebSocketClientProtocol):
    """
    Forward messages from FastAPI WebSocket to websockets client
    """
    try:
        while True:
            message = await src_ws.receive()
            
            if "text" in message and message["text"] is not None:
                await dst_ws.send(message["text"])
            elif "bytes" in message and message["bytes"] is not None:
                await dst_ws.send_bytes(message["bytes"])
            else:
                break
    except Exception as e:
        from core.logger import server_logger
        server_logger.log_event("error", f"fastapi->websockets: {e}")

async def forward_messages_websockets_to_fastapi(src_ws: websockets.WebSocketClientProtocol, dst_ws: WebSocket):
    """
    Forward messages from websockets client to FastAPI WebSocket
    """
    try:
        async for msg in src_ws:
            if isinstance(msg, str):
                await dst_ws.send_text(msg)
            else:
                await dst_ws.send_bytes(msg)
    except Exception as e:
        from core.logger import server_logger
        server_logger.log_event("error", f"websockets->fastapi: {e}")

async def proxy_websocket(ws: WebSocket, target_url: str):
    """
    Proxy WebSocket connection to target URL
    """
    await ws.accept()
    from core.logger import server_logger
    server_logger.log_event("debug", f"Proxy WS connect -> {target_url}")
    try:
        async with websockets.connect(target_url) as target_ws:
            await asyncio.gather(
                forward_messages_fastapi_to_websockets(ws, target_ws),
                forward_messages_websockets_to_fastapi(target_ws, ws)
            )
    except Exception as e:
        from core.logger import server_logger
        server_logger.log_event("debug", f"WebSocket proxy error: {e}")
    finally:
        if not ws.client_state.name == "DISCONNECTED":
            await ws.close()
        server_logger.log_event("debug", f"Proxy WS disconnect -> {target_url}")
