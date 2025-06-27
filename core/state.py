import threading
from typing import Optional
from drivers.igus_scripts.igus_motor import IgusMotor
from drivers.xarm_scripts.XArmManager import XArmManager
from core.logger import server_logger

from core.configuration import symovo_car_ip, symovo_car_number, igus_motor_ip, igus_motor_port, xarm_manipulator_ip
from services.robot_clients import XarmClient
from services.robot_clients import IgusClient
from services.symovo_lib import AgvClient

# Global state variables
job_done = False
thread_work = False
script_stop_event = threading.Event()
thread: Optional[threading.Thread] = None

def init_igus_motor(ip, port):
    global igus_motor,server_logger
    try:
        igus_motor = IgusMotor(ip, port)
        server_logger.log_event("info", "IgusMotor initialized")
    except Exception as e:
        # if e.args[0] == 'Drive reports FAULT bit set' or e.args[0] == 'Timeout waiting for state OPERATION_ENABLED':
        from core.logger import server_logger
        server_logger.log_event("error", f"IgusMotor init failed: {e}")
        try:
            igus_motor._controller.initialize()
        except Exception as init_err:
            server_logger.log_event("error", f"Motor re-init failed: {init_err}")
    return
# Initialize hardware clients
symovo_car = AgvClient(ip=symovo_car_ip, robot_number=symovo_car_number)
# symovo_car.start_polling(interval=10)
server_logger.log_event("info", "Symovo polling started")
xarm_client = XarmClient()
igus_client = IgusClient()
server_logger.log_event("info", "Hardware clients created")
igus_motor: Optional[IgusMotor] = None
init_igus_motor(igus_motor_ip, igus_motor_port)
xarm_manager = XArmManager(ip_address=xarm_manipulator_ip)




