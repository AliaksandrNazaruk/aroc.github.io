from xarm.wrapper import XArmAPI
import threading
from drivers.xarm_scripts.xarm_manipulator import RobotMain

class XArmManager:
    def __init__(self, ip_address):
        self.ip_address = ip_address
        self._lock = threading.RLock()    # <--- исправлено!
        self._instance = None
        self._create_new_instance()

    def get_instance(self, reset: bool = False):
        with self._lock:
            if (
                not reset
                and self._instance is not None
                and self._instance._arm.connected
            ):
                return self._instance
            self._create_new_instance()
            return self._instance

    def _create_new_instance(self):
        self._disconnect_instance()
        arm = XArmAPI(self.ip_address, baud_checkset=False)
        arm.get_robot_sn()
        self._instance = RobotMain(arm)

    def _disconnect_instance(self):
        with self._lock:
            if self._instance:
                try:
                    self._instance._arm.disconnect()
                except Exception:
                    pass
                self._instance = None
