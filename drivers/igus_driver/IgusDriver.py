import socket
import struct
import time
from typing import Optional, List
from drivers.igus_driver.igus_motor_command_builder import MotorCommandBuilder
import drivers.igus_driver.igus_checkers as checkers

def make_bytearray(read_write, obj_ind, sub_ind, data_len, temp_data=[-1, -1, -1, -1]):
    # [transaction_id_1, transaction_id_2,      always 0, 0
    #  protocol_id_1, protocol_id_2, null,      always 0, 0, 0
    #  length,                                  amount of bytes to be sent after b5
    #  null, function_code, mei_type,           always 0, 43, 13
    #  rw_byte,                                 0 for read, 1 for write
    #  null, null,                              always 0, 0
    #  object_index_1, object_index_2,          set the function
    #  sub_index,                               set sub-index of function
    #  null, null, null,                        always 0, 0, 0
    #  bytes_amount,                            amount of data bytes to be sent/received
    #  data_1, data_2, data_3, data_4]          data bytes

    data = []
    for i in temp_data:
        if i != -1:
            data.append(i)

    array = bytearray([0, 0,0, 0, 0,0,0, 43, 13,read_write,0, 0]+ obj_ind +[sub_ind,0, 0, 0,data_len]+ data)

    array[5] = len(array) - 6

    return array

def get_array(selector) -> List[int]:
    if selector == "status":
        sel = make_bytearray(0, [96, 65], 0, 2)
    elif selector == "shutdown":
        sel = make_bytearray(1, [96, 64], 0, 2, [6, 0])
    elif selector == "switch_on":
        sel = make_bytearray(1, [96, 64], 0, 2, [7, 0])
    elif selector == "enable_operation":
        sel = make_bytearray(1, [96, 64], 0, 2, [15, 0])

    return sel

class IgusDriver:
    def __init__(self):
        self._sock: Optional[socket.socket] = None
        self.position = 0
        self.last_recieive = []

    def init_socket(self, ip_address: str, port: int = 502) -> None:
        """
        Initialize and connect a socket to the specified IP address and port.
        
        Args:
            ip_address (str): The IP address to connect to
            port (int, optional): The port number. Defaults to 502.
        
        Raises:
            ConnectionError: If socket creation or connection fails
        """
        try:
            self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._sock.connect((ip_address, port))
        except socket.error as e:
            raise ConnectionError(f"Failed to connect to {ip_address}:{port}. Error: {str(e)}")

    def send_command(self, data: bytes) -> bytes:
        """
        Send a command through the socket and receive the response.
        
        Args:
            data (bytes): The command data to send
            
        Returns:
            bytes: The response from the device
            
        Raises:
            ConnectionError: If socket is not initialized or communication fails
        """
        if self._sock is None:
            raise ConnectionError("Socket not initialized. Call init_socket first.")
        
        try:
            self._sock.send(data)
            self.last_recieive  = self._sock.recv(24)
            return self.last_recieive
        except socket.error as e:
            raise ConnectionError(f"Failed to send/receive data. Error: {str(e)}")

    def close(self) -> None:
        """Close the socket connection."""
        if self._sock is not None:
            self._sock.close()
            self._sock = None

_driver = IgusDriver()

def init_socket(ip_address: str, port: int = 502) -> None:
    _driver.init_socket(ip_address, port)

def send_command(data: bytes) -> bytes:
    return _driver.send_command(data)

def _get_statusword():
    status_bytes = send_command(get_array("status"))
    sw = status_bytes[-2] + (status_bytes[-1] << 8)
    from core.logger import server_logger
    server_logger.log_event("debug", f"Statusword=0x{sw:x}")
    return sw

def get_statusword(status: List[int]) -> Optional[int]:
    """
    Извлечь statusword из ответа контроллера.
    Обычно statusword это два последних байта Modbus ответа.
    """
    if status and len(status) >= 2:
        return status[-2] | (status[-1] << 8)
    return None

def close() -> None:
    _driver.close()

def set_shutdown():
    send_command(get_array("shutdown"))
    MAX_ATTEMPTS = 10
    for timer in range(MAX_ATTEMPTS):
        status = send_command(get_array("status"))
        if checkers.is_shutdown(status):
            return
        from core.logger import server_logger
        server_logger.log_event("debug", f"Waiting for shutdown... statusword={hex(get_statusword(status))}")
        time.sleep(0.3)
    raise Exception(f"Shutdown failed, last statusword={hex(get_statusword(status))}")

def set_switch_on():
    send_command(get_array("switch_on"))
    timer = 0
    status = []
    while not checkers.is_switched_on(status):
        status = send_command(get_array("status"))
        from core.logger import server_logger
        server_logger.log_event("debug", 'Waiting for switch-on...')
        time.sleep(1)
        timer = timer + 1
        if timer > 2:
            raise Exception("Switch-on failed")
        
def set_reset_faults():
    """
    Сброс ошибки контроллера с обязательным возвратом бит 7 controlword в 0 после попытки.
    """
    MAX_ATTEMPTS = 5
    DELAY = 0.3

    for attempt in range(MAX_ATTEMPTS):
        status = send_command(get_array("status"))
        if checkers.is_no_error(status):
            return True

        # 1. Установить бит 7
        send_command(MotorCommandBuilder.fault_reset())
        time.sleep(0.1)
        # 2. Сбросить бит 7 (нормальный controlword, например shutdown)
        send_command(MotorCommandBuilder.shutdown())  # или просто controlword = 0x06 (shutdown)
        from core.logger import server_logger
        server_logger.log_event("debug", f"Waiting for reset faults... (attempt {attempt + 1})")
        time.sleep(DELAY)

    status = send_command(get_array("status"))
    if checkers.is_no_error(status):
        return True

    raise Exception("Reset faults failed")

def full_state_machine_recover():
    send_command(get_array("shutdown"))
    while not checkers.is_shutdown(send_command(get_array("status"))):
        time.sleep(0.1)
    send_command(get_array("switch_on"))
    while not checkers.is_switched_on(send_command(get_array("status"))):
        time.sleep(0.1)
    send_command(MotorCommandBuilder.get_mode(1))
    time.sleep(0.1)
    send_command(get_array("enable_operation"))
    while not checkers.is_operation_enabled(send_command(get_array("status"))):
        time.sleep(1)

    # Проверить homing
    if not get_homing_status():
        set_homing()
  
def set_enable_operation():
    send_command(get_array("enable_operation"))
    timer = 0
    status = []
    while not checkers.is_operation_enabled(status):
        status = send_command(get_array("status"))
        from core.logger import server_logger
        server_logger.log_event("debug", 'Waiting for enabling operation...')
        time.sleep(1)
        timer = timer + 1
        if timer > 2:
            raise Exception("Enabling operation failed")

def init():
    try:
        send_command(MotorCommandBuilder.get_mode(1))
        set_reset_faults()
        set_shutdown()
        set_switch_on()
        set_enable_operation()
        
        
        
        time.sleep(1)
    except Exception as e:
        raise Exception("Initialization failed: "+e.args[0])

def set_feedrate(feedrate):
    feedrate_bytes = feedrate.to_bytes(4, "little")
    send_command(make_bytearray(1, [96, 146], 1, 2, [feedrate_bytes[0],feedrate_bytes[1]]))
    send_command(make_bytearray(1, [96, 146], 2, 1, [1]))

def set_mode(mode):
    send_command(make_bytearray(1, [96, 96], 0, 1, [mode]))

def set_homing():
    try:
        if get_homing_status():
            return True

        send_command(MotorCommandBuilder.get_mode(6))
        time.sleep(1)
        send_command(MotorCommandBuilder.feed_const_1())
        time.sleep(1)
        send_command(MotorCommandBuilder.feed_const_2())
        time.sleep(1)
        send_command(MotorCommandBuilder.homing_speed_switch())
        time.sleep(1)
        send_command(MotorCommandBuilder.homing_speed_zero())
        time.sleep(1)
        send_command(MotorCommandBuilder.homing_acc())
        time.sleep(1)
        send_command(MotorCommandBuilder.start_homing())
        time.sleep(1)

        last_positions = [None, None, None, None]
        while True:
            time.sleep(0.5)
            status = send_command(get_array("status"))
            if checkers.is_fault(status):
                raise Exception("Homing failed: Motor in FAULT state")

            if checkers.is_homing_done(status):
                break

            pos = get_current_position()
            last_positions.pop(0)
            last_positions.append(pos)
            if None not in last_positions and all(x == last_positions[0] for x in last_positions):
                raise Exception("Homing failed: Position stuck")

        set_enable_operation()
        return True
    except Exception as e:
        raise Exception("Homing failed: " + str(e))
   
def move(velocity, acceleration, target_position):
    try:
        set_reset_faults()
        full_state_machine_recover()
        send_command(MotorCommandBuilder.profile_velocity_command(velocity))
        time.sleep(0.05)
        send_command(MotorCommandBuilder.profile_accel_command(acceleration))
        time.sleep(0.05)
        send_command(MotorCommandBuilder.profile_position_command(target_position))
        time.sleep(0.05)
        send_command(MotorCommandBuilder.start_profile_position())

        # Для отлова "застревания"
        last_positions = [None, None, None, None]

        while True:
            time.sleep(0.5)
            status = send_command(get_array("status"))
            if checkers.is_fault(status):
                raise Exception("Move failed: Motor is in FAULT state")

            if checkers.is_moving_done(status):
                _get_statusword()
                break

            pos = get_current_position()
            last_positions.pop(0)
            last_positions.append(pos)

            if (None not in last_positions and
                all(x == last_positions[0] for x in last_positions)):
                raise Exception("Move failed: Position stuck")

        # === Новый кусок: убедиться, что бит 12 снят ===
        # Если бит 12 "Operation Mode Specific" установлен, делаем Enable Operation до сброса
        set_shutdown()
        for i in range(3):  # не более 3 попыток
            status = send_command(get_array("status"))
            sw = status[-2] + (status[-1] << 8)
            if sw & 0x1000:  # бит 12 выставлен
                from core.logger import server_logger
                server_logger.log_event("debug", "Operation Mode Specific активен, отправляю Enable Operation...")
                send_command(get_array("enable_operation"))
                time.sleep(0.1)
            else:
                break
        return True

    except Exception as e:
        raise Exception("Move failed: " + str(e))

def get_status():
    status = []

    actual_position_bytes = send_command(make_bytearray(0, [96, 100], 0, 4))
    status.append(struct.unpack("<xxxxxxxxxxxxxxxxxxxi", actual_position_bytes)[0])

    actual_velocity_bytes = send_command(make_bytearray(0, [96, 108], 0, 4))
    status.append(struct.unpack("<xxxxxxxxxxxxxxxxxxxi", actual_velocity_bytes)[0])

    return status

def get_current_position() -> int:
    try:
        cmd = MotorCommandBuilder.read_actual_position()
        response = send_command(cmd)

        response_data = response[19:23]
        _driver.position = int.from_bytes(response_data, byteorder="little", signed=True)
        # тут можно добавить дополнительные проверки, если нужно
        return _driver.position
    except Exception as e:
        _driver.position = None
        return None

def get_current_velocity() -> int:

    response = send_command(MotorCommandBuilder.read_actual_position())

    response_data = response[19:23]
    position = int.from_bytes(response_data, byteorder="little")

    return position if position <= 120000 else 0

def get_homing_status() -> bool:
    response = send_command(MotorCommandBuilder.get_homing_status())
    return checkers.is_homing_attained(response)