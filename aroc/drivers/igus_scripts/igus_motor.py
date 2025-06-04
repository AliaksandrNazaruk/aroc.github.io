import threading
import queue
import time
from typing import Callable, Any, Optional, Dict
from core.logger import server_logger

from drivers.igus_scripts.igus_modbus_driver import (
    init_socket, close, init, set_homing, move, set_reset_faults,
    _driver, get_current_position, get_homing_status,_get_statusword
)

class IgusCommand:
    def __init__(self, func: Callable, args: tuple = (), kwargs: dict = None, result_queue: Optional[queue.Queue] = None):
        self.func = func
        self.args = args
        self.kwargs = kwargs or {}
        self.result_queue = result_queue

class IgusMotor:
    """Singleton-подход: один объект — одно соединение с мотором."""

    def __init__(self, ip_address: str, port: int = 502):
        self.ip_address = ip_address
        self.port = port

        self._cmd_queue = queue.Queue()
        self._worker_thread = threading.Thread(target=self._worker, daemon=True)
        self._status_lock = threading.Lock()
        self._stop_event = threading.Event()

        # Внутренние состояния
        self._connected = False
        self._active = False
        self._position = 0
        self._homed = False
        self._last_error = None
        self._last_status = None
        self._driver = None
        # Подключение и запуск потока
        self._start_connection()
        if self._connected:
            self._worker_thread.start()
        else:
            raise Exception(f"Failed to connect to {ip_address}:{port}: {self._last_error}")

    def _start_connection(self, retries=3, retry_delay=2):
        for attempt in range(retries):
            try:
                init_socket(self.ip_address, self.port)
                init()
                with self._status_lock:
                    self._homed = get_homing_status()
                    self._position = get_current_position()
                    self._connected = True
                    self._last_error = None
                    self._active = False
                    self._driver = _driver
                return
            except Exception as e:
                with self._status_lock:
                    self._connected = False
                    self._last_error = str(e)
                    self._active = False
                time.sleep(retry_delay)
        # Если не получилось — бросаем ошибку
        raise Exception(f"Failed to connect to {self.ip_address}:{self.port}: {self._last_error}")


    def _worker(self):
        while not self._stop_event.is_set():
            try:
                cmd: IgusCommand = self._cmd_queue.get(timeout=0.1)
            except queue.Empty:
                continue

            try:
                result = cmd.func(*cmd.args, **cmd.kwargs)
                with self._status_lock:
                    # Обновление состояния
                    if cmd.func == set_homing:
                        self._homed = True
                        self._active = True
                        self._position = _driver.position
                    elif cmd.func == move:
                        # move(velocity, accel, target_position)
                        if len(cmd.args) > 2:
                            self._position = cmd.args[2]
                        self._active = False
                    elif cmd.func == set_reset_faults:
                        self._active = False
                    self._last_error = None
                if cmd.result_queue:
                    cmd.result_queue.put((True, result))
            except Exception as e:
                with self._status_lock:
                    self._last_error = str(e)
                    self._connected = False
                    self._active = False
                server_logger.log_event('error', f'IgusMotor worker error: {e}')
                self._reconnect()
                if cmd.result_queue:
                    cmd.result_queue.put((False, e))

    def _reconnect(self):
        try:
            close()
        except Exception:
            pass
        time.sleep(1)
        self._start_connection()

    def shutdown(self):
        """Корректно завершить работу мотора и worker."""
        self._stop_event.set()
        self._worker_thread.join(timeout=2)
        try:
            close()
        except Exception:
            pass
        with self._status_lock:
            self._connected = False
            self._active = False

    # ------------- PUBLIC API -------------
    def fault_reset(self, blocking=True):
        return self._enqueue(set_reset_faults, (), blocking=blocking)

    def home(self, blocking=True):
        return self._enqueue(set_homing, (), blocking=blocking)

    def move_to_position(self, target_position, velocity=5000, acceleration=1000, blocking=True):
        with self._status_lock:
            if not self._homed:
                raise Exception("Movement impossible: Homing required first.")
        return self._enqueue(move, (velocity, acceleration, target_position), blocking=blocking)

    # --- State getters ---
    def get_position(self):
        with self._status_lock:
            self._position = _driver.position
            return self._position

    def is_homed(self):
        with self._status_lock:
            return self._homed

    def is_active(self):
        with self._status_lock:
            return self._active
        
    def get_statusword(self):
        return _get_statusword()
    
    def get_error(self):
        with self._status_lock:
            return self._last_error

    def is_connected(self):
        with self._status_lock:
            return self._connected

    def get_status(self) -> Dict[str, Any]:
        with self._status_lock:
            return {
                "position": self._position,
                "homed": self._homed,
                "active": self._active,
                "last_error": self._last_error,
                "connected": self._connected,
            }

    # --- Helpers ---
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

    # context manager support
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.shutdown()


# === Пример использования ===
if __name__ == "__main__":
    from core.connection_config import igus_motor_ip, igus_motor_port
    motor = IgusMotor(igus_motor_ip, igus_motor_port)
    position = 5000
    try:
        if motor.is_homed():
            motor.move_to_position(position , velocity=5000, acceleration=1000)
        else:
            motor.home()
        print("[Demo] Переместился в "+str(position))
    except Exception as e:
        print(f"[Demo] Ошибка: {e}")
    finally:
        motor.shutdown()
