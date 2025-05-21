import asyncio
import json
import logging
import websockets
from low_level.igus_scripts.igus_modbus_driver import IgusMotorController, IgusMotorError, MotorCommandBuilder
import time
from configuration import igus_motor_port, igus_motor_ip, igus_ws_host, igus_ws_port
from typing import Set, Optional
import ipaddress
from dataclasses import dataclass

logging.basicConfig(level=logging.DEBUG)

class MotorWebSocketServer:
    """
    WebSocket server for monitoring motor state.
    Handles state updates and broadcasts them to connected clients.
    """
    def __init__(
        self,
        motor_ip: str,
        motor_port: int,
        ws_host: str,
        ws_port: int,
        max_connections: int = 100,
        connection_timeout: float = 30.0
    ):
        try:
            ipaddress.ip_address(motor_ip)
        except ValueError:
            raise ValueError(f"Invalid IP address: {motor_ip}")
            
        if not 0 <= motor_port <= 65535:
            raise ValueError(f"Invalid port number: {motor_port}")
            
        self.motor_ip = motor_ip
        self.motor_port = motor_port
        self.ws_host = ws_host
        self.ws_port = ws_port
        self.max_connections = max_connections
        self.connection_timeout = connection_timeout
        self.clients: Set[websockets.WebSocketServerProtocol] = set()
        self.broadcast_task: Optional[asyncio.Task] = None
        self.server: Optional[websockets.WebSocketServer] = None
        
    async def _get_motor_state(self) -> dict:
        """
        Get current motor state by connecting, reading state, and disconnecting.
        """
        motor_controller = None
        try:
            # Create and connect to motor
            motor_controller = await asyncio.to_thread(IgusMotorController, self.motor_ip, self.motor_port)

            # Read state
            position = await asyncio.to_thread(motor_controller.get_current_position)
            active = await asyncio.to_thread(motor_controller.get_motor_state)
            ready = await asyncio.to_thread(motor_controller._is_ready)
            error = await asyncio.to_thread(motor_controller._check_error)
            homing = await asyncio.to_thread(motor_controller._check_homing_status)
            
            return {
                "position": position,
                "active": active,
                "ready": ready,
                "error": error,
                "homing": homing,
                "connected": True
            }
        except Exception as e:
            raise Exception("Igus library internal error")
        finally:
            # Always disconnect
            if motor_controller:
                try:
                    await asyncio.to_thread(motor_controller.disconnect)
                except Exception as e:
                    logging.error(f"Error disconnecting from motor: {e}")

    async def broadcast_status(self, update_interval: float = 1) -> None:
        while True:
            try:
                clients_snapshot = list(self.clients)
                if not clients_snapshot:
                    await asyncio.sleep(update_interval)
                    continue

                # Get motor state
                motor_state = await self._get_motor_state()

                # Prepare update message
                data = {
                    "command": "status_update",
                    "data": {
                        **motor_state,
                        "timestamp": time.time()
                    }
                }

                # Send to clients with error handling
                disconnected_clients = set()
                for client in clients_snapshot:
                    try:
                        await client.send(json.dumps(data))
                    except websockets.exceptions.ConnectionClosed:
                        disconnected_clients.add(client)
                    except Exception as e:
                        logging.error(f"Error sending to client: {e}")
                        disconnected_clients.add(client)

                # Clean up disconnected clients
                self.clients -= disconnected_clients

            except Exception as e:
                logging.error(f"Error in broadcast loop: {e}")
                await asyncio.sleep(1)  # Backoff on error

            await asyncio.sleep(update_interval)

    async def handler(self, websocket: websockets.WebSocketServerProtocol, path: str) -> None:
        if len(self.clients) >= self.max_connections:
            await websocket.close(code=1008, reason="Server is at capacity")
            return

        try:
            self.clients.add(websocket)
            logging.info(f"Client connected: {websocket.remote_address}")
            
            async for message in websocket:
                try:
                    if len(message) > 1024:  # Message size limit
                        await websocket.send(json.dumps({
                            "error": "Message too large"
                        }))
                        continue

                    data = json.loads(message)
                    if not isinstance(data, dict):
                        raise ValueError("Invalid message format")

                    if data.get("type") == "ping":
                        await websocket.send(json.dumps({"type": "pong"}))

                except json.JSONDecodeError:
                    await websocket.send(json.dumps({
                        "error": "Invalid JSON"
                    }))
                except Exception as e:
                    logging.error(f"Error processing message: {e}")

        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            self.clients.discard(websocket)
            logging.info(f"Client disconnected: {websocket.remote_address}")

    async def run_server(self) -> None:
        try:
            logging.info(f"Starting WebSocket server on {self.ws_host}:{self.ws_port}")
            
            # Start status broadcasting
            self.broadcast_task = asyncio.create_task(self.broadcast_status())
            
            # Start WebSocket server
            self.server = await websockets.serve(
                self.handler,
                self.ws_host,
                self.ws_port,
                ping_interval=10,
                ping_timeout=10,
                close_timeout=5,
                max_size=1024 * 1024,  # 1MB message size limit
                max_queue=32,  # Maximum number of queued messages
            )
            
            await self.server.wait_closed()
            
        except Exception as e:
            logging.critical(f"Server startup failed: {e}")
            raise
        finally:
            # Cleanup
            if self.broadcast_task:
                self.broadcast_task.cancel()
                try:
                    await self.broadcast_task
                except asyncio.CancelledError:
                    pass
            
            if self.server:
                self.server.close()
                await self.server.wait_closed()

def main():
    logging.basicConfig(
        filename="igus_logs.log",
        level=logging.DEBUG,
        format="%(asctime)s %(levelname)s: %(message)s"
    )

    server = MotorWebSocketServer(igus_motor_ip, igus_motor_port, igus_ws_host, igus_ws_port)
    try:
        asyncio.run(server.run_server())
    except KeyboardInterrupt:
        logging.info("Server stopped by user")
    except Exception as e:
        logging.critical("Critical WebSocket server error: %s", e)

if __name__ == "__main__":
    main()