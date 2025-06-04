# websocket_handlers.py
import logging
import asyncio

logger = logging.getLogger("websocket_handlers")

connected_color_clients = set()
connected_depth_clients = set()


async def websocket_handler(websocket, stream_type):
    client_addr = websocket.remote_address
    clients = connected_color_clients if stream_type == 'color' else connected_depth_clients
    clients.add(websocket)
    client_ip = websocket.remote_address[0] if websocket.remote_address else "unknown"
    logger.info(f"Client connected: {client_ip}, total clients: {len(clients)}")
    try:
        # Просто ждем закрытия соединения (ничего не отправляем из этого корутина напрямую)
        await websocket.wait_closed()
    except asyncio.CancelledError:
        logger.info(f"[WS-{stream_type.upper()}] Задача отменена для клиента {client_addr}")

    except Exception as e:
        logger.error(f"[{stream_type.upper()}] Ошибка соединения с клиентом {websocket.remote_address}: {e}")

    finally:
        clients.discard(websocket)
        logger.info(f"[{stream_type.upper()}] Отключен клиент {websocket.remote_address}")

# Обработчики, запускаемые из main
async def handle_color_connection(websocket):
    await websocket_handler(websocket, "color")

async def handle_depth_connection(websocket):
    await websocket_handler(websocket, 'depth')
