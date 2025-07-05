import threading
from typing import Optional
from models.task_manager import TaskManager
from drivers.igus_driver.IgusMotorManager import IgusMotorManager
from drivers.xarm_driver.XArmManager import XArmManager
from core.logger import server_logger
from typing import Dict

from core.configuration import symovo_car_ip, symovo_car_number, igus_motor_ip, igus_motor_port, xarm_manipulator_ip

from services.robot_clients import XarmClient
from services.robot_clients import IgusClient
from services.symovo_lib import AgvClient

task_manager = TaskManager()
igus_manager = IgusMotorManager(ip_address=igus_motor_ip, port=igus_motor_port)
xarm_manager = XArmManager(ip_address=xarm_manipulator_ip)

# symovo_car.start_polling(interval=10)
xarm_client = XarmClient()
igus_client = IgusClient()
symovo_client = AgvClient(ip=symovo_car_ip, robot_number=symovo_car_number)


virtual_joysticks: Dict[str, dict] = {}
server_logger.log_event("info", "Hardware clients created")







