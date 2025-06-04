import sys
import time
import traceback
from drivers.igus_scripts.igus_modbus_driver import IgusMotorController, MotorCommandBuilder
from core.configuration import igus_motor_ip, igus_motor_port, igus_ws_host, igus_ws_port

class RobotMain(object):
    """Robot Main Class"""
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

    # Robot Main Run
    def run(self, data=None):
        try:
            return True
        except Exception as e:
            self.pprint('MainException: {}'.format(e))
            return False
        finally:
            # Cleanup in finally block to ensure it always happens
            self._motor.shutdown()
            self.alive = False
            # Release all callbacks
            self._motor.release_error_warn_changed_callback(self._error_warn_changed_callback)
            self._motor.release_state_changed_callback(self._state_changed_callback)
            if hasattr(self._motor, 'release_count_changed_callback'):
                self._motor.release_count_changed_callback(self._count_changed_callback)
        
        return 'error'
