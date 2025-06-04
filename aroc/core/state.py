import threading
from typing import Optional
from drivers.igus_scripts.igus_motor import IgusMotor

from core.configuration import symovo_car_ip, symovo_car_number, igus_motor_ip, igus_motor_port
from services.robot_lib import XarmClient
from services.robot_lib import IgusClient
from services.symovo_lib import AgvClient

# Global state variables
job_done = False
thread_work = False
script_stop_event = threading.Event()
thread: Optional[threading.Thread] = None


# Initialize hardware clients
symovo_car = AgvClient(ip=symovo_car_ip, robot_number=symovo_car_number)
xarm_client = XarmClient()
igus_client = IgusClient()

igus_motor: Optional[IgusMotor] = None

def init_igus_motor(ip, port):
    global igus_motor
    igus_motor = IgusMotor(ip, port)
    return

symovo_car.start_polling(interval=10)


server_logger = None
