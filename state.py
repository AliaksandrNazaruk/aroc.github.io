import threading
from typing import Optional
from datetime import datetime
import middle_level.symovo_lib as symovo_lib
import middle_level.igus_lib as igus_lib
from configuration import symovo_car_ip, symovo_car_number, igus_motor_ip, igus_motor_port

# Global state variables
job_done = False
thread_work = False
script_stop_event = threading.Event()
thread: Optional[threading.Thread] = None

# Script status management
script_statuses = ["WORKING", "FINISHED", "NOT_RUNING", "STOPPED", "FAILED"]
script_status = script_statuses[3]

# Initialize hardware clients
symovo_car = symovo_lib.AgvClient(ip=symovo_car_ip, robot_number=symovo_car_number)
symovo_car.start_polling(interval=10)

igus_motor = igus_lib.IgusClient(ip=igus_motor_ip, port=igus_motor_port)
igus_motor.start_polling(interval=3)

# Server logger instance (will be initialized in logger.py)
server_logger = None
