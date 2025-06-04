import sys
import time
import traceback
from drivers.igus_scripts.igus_modbus_driver import IgusMotorController, MotorCommandBuilder
from core.configuration import igus_motor_ip, igus_motor_port, igus_ws_host, igus_ws_port
from concurrent.futures import ThreadPoolExecutor, Future
from typing import Optional

class RobotMain(object):
    """Robot Main Class"""
    _executor: ThreadPoolExecutor = ThreadPoolExecutor(max_workers=1)
    def __init__(self, robot, **kwargs):
        
        self.alive = True
        self._motor = robot
        self._tcp_speed = 100
        self._tcp_acc = 2000
        self._angle_speed = 20
        self._angle_acc = 500
        self._vars = {}
        self._funcs = {}
        self._robot_init()

    # Robot init
    def _robot_init(self):
        
        self._motor.reset_faults()
        self._motor.shutdown()
        self._motor.switch_on()
        self._motor.send_command(MotorCommandBuilder.get_mode(1))
        self._motor.enable_operation(0)
        
        time.sleep(1)
        # self._motor.register_error_warn_changed_callback(self._error_warn_changed_callback)
        # self._motor.register_state_changed_callback(self._state_changed_callback)
        # if hasattr(self._motor, 'register_count_changed_callback'):
        #     self._motor.register_count_changed_callback(self._count_changed_callback)

    # Register error/warn changed callback
    def _error_warn_changed_callback(self, data):
        if data and data.error_code != 0:
            self.alive = False
            self.pprint('err={}, quit'.format(data.error_code))

    # Register state changed callback
    def _state_changed_callback(self, data):
        if data and data.state == 4:
            self.alive = False
            self.pprint('state=4, quit')

    # Register count changed callback
    def _count_changed_callback(self, data):
        if self.is_alive:
            self.pprint('counter val: {}'.format(data.count))

    def _check_code(self, code, label):
        if not self.is_alive or code != 0:
            self.alive = False
            ret1 = self._motor.get_state()
            ret2 = self._motor.get_err_warn_code()
            self.pprint('{}, code={}, connected={}, state={}, error={}, ret1={}. ret2={}'.format(label, code, self._motor.connected, self._motor.state, self._motor.error_code, ret1, ret2))
        return self.is_alive

    @staticmethod
    def pprint(*args, **kwargs):
        try:
            stack_tuple = traceback.extract_stack(limit=2)[0]
            print('[{}][{}] {}'.format(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())), stack_tuple[1], ' '.join(map(str, args))))
        except:
            print(*args, **kwargs)

    @property
    def motor(self):
        return self._motor

    @property
    def VARS(self):
        return self._vars

    @property
    def FUNCS(self):
        return self._funcs

    @property
    def is_alive(self):
        if self.alive and self._motor.connected and self._motor.error_code == 0:
            if self._motor._is_ready():
                return True
        else:
            return False

    # -----------------------------------------------------------------
    def _do_move(self, data: dict) -> bool:

        try:
            result = self._motor.move_to_position(
                int(data['position']),
                int(data['velocity']),
                int(data['acceleration'])
            )
            return result
        except Exception as e:
            self.pprint(f"MainException: {e}")
            return False
        finally:
            # освобождаем ресурсы, как было раньше
            self._motor.shutdown()
            self.alive = False
            self._motor.release_error_warn_changed_callback(
                self._error_warn_changed_callback
            )
            self._motor.release_state_changed_callback(
                self._state_changed_callback
            )
            if hasattr(self._motor, 'release_count_changed_callback'):
                self._motor.release_count_changed_callback(
                    self._count_changed_callback
                )

    # Robot Main Run
                
                
    def run(self, data: Optional[dict] = None):
        """
        Если data['wait'] == True  – блокирующий вызов (старое поведение).
        Если data['wait'] == False – запуск в фоне, метод сразу возвращает Future.
        """
        data = data or {}

        # По-умолчанию ждём (старое поведение)
        wait_flag = data.get('wait', True)

        # Блокирующий сценарий – ровно как раньше
        if wait_flag:
            return self._do_move(data)

        # Асинхронный сценарий
        future: Future = self._executor.submit(self._do_move, data)
        # Можно подписаться на ошибки / отчёты:
        # future.add_done_callback(lambda f: self.pprint(f"Задача окончена, результат: {f.result()}"))
        return future


# data = {
#     "command": "move_to_position",
#     "position": 0,
#     "velocity": 5000,
#     "acceleration": 5000,
#     "wait": True
# }

# motor_controller = IgusMotorController(igus_motor_ip)
# robot_main = RobotMain(motor_controller)
# robot_main.run(data)