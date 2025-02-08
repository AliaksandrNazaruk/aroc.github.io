import socket
import psutil
import os
import logging
import asyncio
import websockets
clients = set()

def is_port_in_use(port: int) -> bool:
    """Проверяет, используется ли указанный порт."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('0.0.0.0', port)) == 0

def kill_process_using_port(port: int) -> bool:
    """Завершает процесс, использующий указанный порт."""
    for conn in psutil.net_connections():
        if conn.laddr.port == port:
            pid = conn.pid
            if pid:
                try:
                    os.kill(pid, 9)
                    logging.info(f"Процесс с PID {pid}, использующий порт {port}, завершен.")
                    return True
                except Exception as e:
                    logging.error(f"Не удалось завершить процесс с PID {pid}: {e}")
    return False

async def handle_client(websocket):
    try:
        clients.add(websocket)
        await websocket.wait_closed()
    except Exception as e:
        logging.error(f"Ошибка в WebSocket обработчике: {e}")
    finally:
        clients.discard(websocket)  # Безопасный вариант удаления

async def send_data_to_clients(data):
    tasks = [client.send(data) for client in clients.copy()]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    for client, result in zip(clients.copy(), results):
        if isinstance(result, websockets.exceptions.ConnectionClosed):
            clients.discard(client)
