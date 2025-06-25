import threading
import queue
import time
from typing import Callable, Any, Optional, Dict
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + "/../.."))

from drivers.igus_scripts.transport import ModbusTcpTransport
from drivers.igus_scripts.protocol import DryveSDO
from drivers.igus_scripts.machine import DriveStateMachine
from drivers.igus_scripts.controller import DryveController

class IgusCommand:
    def __init__(self, func: Callable, args: tuple = (), kwargs: dict = None, result_queue: Optional[queue.Queue] = None):
        self.func = func
        self.args = args
        self.kwargs = kwargs or {}
        self.result_queue = result_queue

class IgusMotor:
    """
    Singleton-объект для dryve D1: работает через новый стек, но с совместимым API.
    """

    def __init__(
        self,
        ip_address: str,
        port: int = 502,
        connect_retries: int = 3,
        retry_delay: float = 3.0,
        reconnect_interval: float = 5.0,
    ):
        self.ip_address = ip_address
        self.port = port

        self._transport = None
        self._sdo = None
        self._fsm = None
        self._controller = None
        self._cmd_queue = queue.Queue()
        self._worker_thread = threading.Thread(target=self._worker, daemon=True)
        self._connection_thread = None
        self._status_lock = threading.Lock()
        self._stop_event = threading.Event()

        # Внутренние состояния (кэш, не опрашивается лишний раз!)
        self._connected = False
        self._active = False
        self._position = 0.0
        self._homed = False
        self._last_error = None
        self._statusword = 0
        self._last_status = None
        self._controller = None

        # Connection management parameters
        self._connect_retries = connect_retries
        self._retry_delay = retry_delay
        self._reconnect_interval = reconnect_interval

        self._start_connection_thread()

    def _start_connection_thread(self) -> None:
        """Launch a background thread that keeps trying to connect."""
        if self._connection_thread and self._connection_thread.is_alive():
            return
        self._connection_thread = threading.Thread(
            target=self._connection_loop, daemon=True
        )
        self._connection_thread.start()

    def _connection_loop(self) -> None:
        """Background connection attempts without blocking the caller."""
        while not self._stop_event.is_set():
            try:
                self._start_connection(
                    retries=self._connect_retries, retry_delay=self._retry_delay
                )
                if self._connected and not self._worker_thread.is_alive():
                    self._worker_thread = threading.Thread(
                        target=self._worker, daemon=True
                    )
                    self._worker_thread.start()
                return
            except Exception as e:
                with self._status_lock:
                    self._last_error = str(e)
                    self._connected = False
                    self._active = False
            time.sleep(self._reconnect_interval)

    def _start_connection(self, retries: int = 3, retry_delay: float = 3.0):
        """Attempt to establish connection with limited retries.

        If all attempts fail an exception is raised.  The previous implementation
        looped forever which blocked server startup when the motor was
        unreachable."""

        last_error = None
        for _ in range(retries):
            try:
                # ------> ВАЖНО! Не with, а явное создание!
                self._transport = ModbusTcpTransport(self.ip_address, self.port)
                self._transport.connect()
                self._sdo = DryveSDO(self._transport)
                self._fsm = DriveStateMachine(self._sdo)
                self._controller = DryveController(self._sdo, self._fsm)
                self._controller.initialize()
                with self._status_lock:
                    self._connected = True
                    self._last_error = None
                return
            except Exception as e:
                last_error = str(e)
                with self._status_lock:
                    self._connected = False
                    self._last_error = last_error
                    self._active = False
                try:
                    if self._transport:
                        self._transport.close()
                except Exception:
                    pass
                time.sleep(retry_delay)

        raise Exception(
            f"Failed to connect to {self.ip_address}:{self.port} after {retries} attempts: {last_error}"
        )
    def _worker(self):
        while not self._stop_event.is_set():
            try:
                cmd: IgusCommand = self._cmd_queue.get(timeout=0.1)
            except queue.Empty:
                continue
            try:
                result = cmd.func(*cmd.args, **cmd.kwargs)
                self._last_error = None
                if cmd.result_queue:
                    cmd.result_queue.put((True, result))
            except Exception as e:
                with self._status_lock:
                    self._last_error = str(e)
                    self._connected = False
                    self._active = False
                # server_logger.log_event('error', f'IgusMotor worker error: {e}')

                self._reconnect()
                if cmd.result_queue:
                    cmd.result_queue.put((False, e))

    def _reconnect(self):
        """Force a reconnect attempt in the background."""
        try:
            if self._transport:
                self._transport.close()
        except Exception:
            pass
        with self._status_lock:
            self._connected = False
            self._active = False
        self._start_connection_thread()

    def shutdown(self):
        self._stop_event.set()
        if self._connection_thread and self._connection_thread.is_alive():
            self._connection_thread.join(timeout=2)
        if self._worker_thread.is_alive():
            self._worker_thread.join(timeout=2)
        try:
            if self._transport:
                self._transport.close()
        except Exception:
            pass
        with self._status_lock:
            self._connected = False
            self._active = False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.shutdown()

    # ------------- PUBLIC API -------------
    def home(self, blocking=True):
        result = self._enqueue(self._controller.home, (), blocking=blocking)
        return result

    def move_to_position(self, target_position, velocity=2000, acceleration=2000, blocking=True):
        with self._status_lock:
            if not self._controller.is_homed:
                raise Exception("Movement impossible: Homing required first.")
        result = self._enqueue(
            self._controller.move_to_position,(target_position, velocity, acceleration),blocking=blocking,)
        return result

    def fault_reset(self, blocking=True):
        result = self._enqueue(self._controller.initialize, (), blocking=blocking)
        return result

    # --- State getters ---


    def get_statusword(self):
        with self._status_lock:
            return self._controller.get_statusword()

    def get_status(self) -> Dict[str, Any]:
        self._controller.get_error()
        with self._status_lock:
            return {
                "position": self._controller.position,
                "homed": self._controller.is_homed,
                "active": self._controller.is_motion,
                "error_state": self._controller.error_state,
                "connected": True,
                "statusword": self._controller.statusword,
            }


    def _enqueue(self, func, args, blocking=True):
        result_queue = queue.Queue(maxsize=1) if blocking else None
        cmd = IgusCommand(func, args, {}, result_queue)
        self._cmd_queue.put(cmd)
        if blocking:
            ok, result = result_queue.get()
            if ok:
                return result
            else:
                raise result
        return None

# === Пример использования ===
if __name__ == "__main__":
    import logging

    logging.basicConfig(
        level=logging.DEBUG,  # или INFO для менее подробных логов
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )
    motor = IgusMotor("127.0.0.1", 502)
    position = 30000
        # motor.get_statusword()
        
    # motor.fault_reset()
    motor.home()

    while True:
        from core.logger import server_logger
        try:
            motor.move_to_position(0)
            server_logger.log_event("info", str(motor.get_status()))
            motor.move_to_position(10000)
            server_logger.log_event("info", str(motor.get_status()))
        except Exception as e:
            server_logger.log_event("error", f"Move demo failed: {e}")
            # if e.args[0] == 'Drive reports FAULT bit set' or e.args[0] == 'Timeout waiting for state OPERATION_ENABLED':
            try:
                server_logger.log_event("debug", str(motor.get_status()))
                motor._controller.initialize()
                if not motor._controller.is_homed:
                    motor.home()
            except Exception as init_err:
                server_logger.log_event("error", f"Init after fail failed: {init_err}")
