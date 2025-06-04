import asyncio
import logging

logger = logging.getLogger("ConnectionManager")

class ConnectionManager:
    def __init__(self, name=""):
        self.clients = set()
        self.lock = asyncio.Lock()
        self.name = name

    async def register(self, websocket):
        async with self.lock:
            self.clients.add(websocket)
            logger.info(f"[{self.name.upper()}] Клиент подключён: {websocket.remote_address}. Всего клиентов: {len(self.clients)}")

    async def unregister(self, websocket):
        async with self.lock:
            self.clients.discard(websocket)
            logger.info(f"[{self.name.upper()}] Клиент отключён: {websocket.remote_address}. Всего клиентов: {len(self.clients)}")

    async def broadcast(self, message):
        async with self.lock:
            to_remove = []
            send_tasks = []
            for ws in self.clients:
                send_tasks.append(self._safe_send(ws, message))
            results = await asyncio.gather(*send_tasks, return_exceptions=True)
            for ws, result in zip(list(self.clients), results):
                if isinstance(result, Exception):
                    to_remove.append(ws)
            for ws in to_remove:
                self.clients.discard(ws)
                logger.info(f"[{self.name.upper()}] Удалён клиент {ws.remote_address} из-за ошибки.")

    async def _safe_send(self, ws, message):
        try:
            await ws.send(message)
        except OSError as e:
            # Логируем ошибку и возвращаем исключение для последующего удаления клиента
            logger.error(f"OSError при отправке клиенту {ws.remote_address}: {e}")
            raise
        except Exception as e:
            logger.error(f"Ошибка при отправке клиенту {ws.remote_address}: {e}")
            raise

