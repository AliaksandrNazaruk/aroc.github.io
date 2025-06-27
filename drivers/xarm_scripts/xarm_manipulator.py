#!/usr/bin/env python3
# Software License Agreement (BSD License)
#
# Copyright (c) 2022, UFACTORY, Inc.
# All rights reserved.
#
# Author: Vinman <vinman.wen@ufactory.cc> <vinman.cub@gmail.com>

"""
# Notice
#   1. Changes to this file on Studio will not be preserved
#   2. The next conversion will overwrite the file with the same name
# 
# xArm-Python-SDK: https://github.com/xArm-Developer/xArm-Python-SDK
#   1. git clone git@github.com:xArm-Developer/xArm-Python-SDK.git
#   2. cd xArm-Python-SDK
#   3. python setup.py install
"""
import time
import traceback
from xarm import version
from xarm.wrapper import XArmAPI
import sys
from drivers.xarm_scripts.xarm_positions import poses
from drivers.xarm_scripts.picobot_lib import GripperController
from pydantic import BaseModel, Field
from drivers.xarm_scripts import xarm_positions

class XarmJointsDict(BaseModel):
    j1: float
    j2: float
    j3: float
    j4: float
    j5: float
    j6: float

class RobotMain(object):
    """Robot Main Class"""
    def __init__(self, robot, **kwargs):
        self.alive = True
        self._arm = robot
        self._tcp_speed = 100
        self._tcp_acc = 2000
        self._angle_speed = 20
        self._angle_acc = 500
        self._vars = {}
        self._funcs = {}
        self._robot_init()
        try:
            self.gripper = GripperController(robot, baudrate=115200, timeout=100)
        except:
            print("Gripper is not available")

    def _robot_init(self):
        self._arm.clean_warn()
        self._arm.clean_error()
        self._arm.motion_enable(True)
        self._arm.set_mode(0)
        self._arm.set_state(0)
        time.sleep(1)
        self._arm.register_error_warn_changed_callback(self._error_warn_changed_callback)
        self._arm.register_state_changed_callback(self._state_changed_callback)
        if hasattr(self._arm, 'register_count_changed_callback'):
            self._arm.register_count_changed_callback(self._count_changed_callback)

    def _error_warn_changed_callback(self, data):
        if data and data['error_code'] != 0:
            self.alive = False
            self.pprint('err={}, quit'.format(data['error_code']))
            self._arm.release_error_warn_changed_callback(self._error_warn_changed_callback)

    def _state_changed_callback(self, data):
        if data and data['state'] == 4:
            self.alive = False
            self.pprint('state=4, quit')
            self._arm.release_state_changed_callback(self._state_changed_callback)

    def _count_changed_callback(self, data):
        if self.is_alive:
            self.pprint('counter val: {}'.format(data['count']))

    def _check_code(self, code, label):
        if not self.is_alive or code != 0:
            self.alive = False
            ret1 = self._arm.get_state()
            ret2 = self._arm.get_err_warn_code()
            self.pprint('{}, code={}, connected={}, state={}, error={}, ret1={}. ret2={}'.format(label, code, self._arm.connected, self._arm.state, self._arm.error_code, ret1, ret2))
        return self.is_alive

    @staticmethod
    def pprint(*args, **kwargs):
        from core.logger import server_logger
        try:
            stack_tuple = traceback.extract_stack(limit=2)[0]
            msg = '[{}][{}] {}'.format(
                time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())),
                stack_tuple[1],
                ' '.join(map(str, args))
            )
        except Exception:
            msg = ' '.join(map(str, args))
        server_logger.log_event("info", msg)

    @property
    def arm(self):
        return self._arm

    @property
    def VARS(self):
        return self._vars

    @property
    def FUNCS(self):
        return self._funcs

    @property
    def is_alive(self):
        if self.alive and self._arm.connected and self._arm.error_code == 0:
            if self._arm.state == 5:
                cnt = 0
                while self._arm.state == 5 and cnt < 5:
                    cnt += 1
                    time.sleep(0.1)
            return self._arm.state < 4
        else:
            return False

    def complex_move_with_joints(self,data):
        _error = None
        try:
            self._arm.set_mode(0)
            self._arm.set_state(0)
            self._angle_speed = int(data.velocity)
            self._angle_acc = int(data.velocity)
            if not self.is_alive:
                raise RuntimeError("manipulator is not alive")
            for joints in data.points:
                code = self._arm.set_servo_angle(angle=[joints.j1, joints.j2, joints.j3, joints.j4, joints.j5, joints.j6], speed=self._angle_speed, mvacc=self._angle_acc, wait=True, radius=-1.0)
                if not self._check_code(code, 'set_position'):
                    raise RuntimeError(f"set_servo_angle, code:{code}")
            return True
        except Exception as e:
            from core.logger import server_logger
            server_logger.log_event("error", f"change position: {e}")
            _error = e

        self.alive = False
        self._arm.release_error_warn_changed_callback(self._error_warn_changed_callback)
        self._arm.release_state_changed_callback(self._state_changed_callback)
        if hasattr(self._arm, 'release_count_changed_callback'):
            self._arm.release_count_changed_callback(self._count_changed_callback)
        raise RuntimeError(f"move_to_pose failed: {_error}")
    
    def move_with_joints(self,data):
        _error = None
        try:
            self._arm.set_mode(0)
            self._arm.set_state(0)
            self._angle_speed = int(data.velocity)
            self._angle_acc = int(data.velocity)
            if not self.is_alive:
                raise RuntimeError("manipulator is not alive")
            code = self._arm.set_servo_angle(angle=[data.j1, data.j2, data.j3, data.j4, data.j5, data.j6], speed=self._angle_speed, mvacc=self._angle_acc, wait=True, radius=-1.0)
            if not self._check_code(code, 'set_position'):
                raise RuntimeError(f"set_servo_angle, code:{code}")
            return True
        except Exception as e:
            from core.logger import server_logger
            server_logger.log_event("error", f"change position: {e}")
            _error = e

        self.alive = False
        self._arm.release_error_warn_changed_callback(self._error_warn_changed_callback)
        self._arm.release_state_changed_callback(self._state_changed_callback)
        if hasattr(self._arm, 'release_count_changed_callback'):
            self._arm.release_count_changed_callback(self._count_changed_callback)
        raise RuntimeError(f"move_to_pose failed: {_error}")
    
    def move_to_pose(self,data):
        _error = None
        try:
            if data.pose_name is None:
                raise RuntimeError("pose name is None")
            self._arm.set_mode(0)
            self._arm.set_state(0)
            self._angle_speed = int(data.velocity)
            self._angle_acc = int(data.velocity)
            if not self.is_alive:
                raise RuntimeError("manipulator is not alive")
            position = poses[data.pose_name]
            code = self._arm.set_servo_angle(angle=[position["j1"], position["j2"], position["j3"], position["j4"], position["j5"], position["j6"]], speed=self._angle_speed, mvacc=self._angle_acc, wait=True, radius=-1.0)
            if not self._check_code(code, 'set_position'):
                raise RuntimeError(f"set_servo_angle, code:{code}")
            return True
        except Exception as e:
            from core.logger import server_logger
            server_logger.log_event("error", f"change position: {e}")
            _error = e

        self.alive = False
        self._arm.release_error_warn_changed_callback(self._error_warn_changed_callback)
        self._arm.release_state_changed_callback(self._state_changed_callback)
        if hasattr(self._arm, 'release_count_changed_callback'):
            self._arm.release_count_changed_callback(self._count_changed_callback)
        raise RuntimeError(f"move_to_pose failed: {_error}")
    
    def move_tool_position(self,data=None):
        _error = None
        try:
            self._arm.set_mode(0)
            self._arm.set_state(0)
            if not self.is_alive:
                raise RuntimeError("manipulator is not alive")
            self._angle_speed = int(data.velocity)
            self._angle_acc = int(data.velocity)
            code = self._arm.set_tool_position(z=int(data.z_offset),y=int(data.y_offset),x=int(data.x_offset), radius=0, speed=self._tcp_speed, mvacc=self._tcp_acc, relative=True, wait=True)
            if not self._check_code(code, 'set_position'):
                raise RuntimeError(f"set_tool_position, code:{code}")
            return True
        except Exception as e:
            from core.logger import server_logger
            server_logger.log_event("error", f"change position: {e}")
            _error = e

        self.alive = False
        self._arm.release_error_warn_changed_callback(self._error_warn_changed_callback)
        self._arm.release_state_changed_callback(self._state_changed_callback)
        if hasattr(self._arm, 'release_count_changed_callback'):
            self._arm.release_count_changed_callback(self._count_changed_callback)
        raise RuntimeError(f"move_tool_position failed: {_error}")

    def drop(self):
        return True
        _error = None
        try:
            code = self.gripper.deactivate()
            if code == [1, 8, 0, 1, 0, 0, 41, 1, 0, 0, 220]:
                return True
            else:
                raise RuntimeError("drop failed")
        except Exception as e:
            from core.logger import server_logger
            server_logger.log_event("error", f"suction_error: {e}")
            _error = e

        self.alive = False
        self._arm.release_error_warn_changed_callback(self._error_warn_changed_callback)
        self._arm.release_state_changed_callback(self._state_changed_callback)
        if hasattr(self._arm, 'release_count_changed_callback'):
            self._arm.release_count_changed_callback(self._count_changed_callback)
        raise RuntimeError(f"suction_error: {_error}")
    
    def take(self):
        return True
        _error = None
        try:
            code = self.gripper.activate()
            if code == [1, 8, 0, 1, 0, 0, 41, 1, 0, 0, 220]:
                return True
            else:
                raise RuntimeError("take failed")
        except Exception as e:
            from core.logger import server_logger
            server_logger.log_event("error", f"suction_error: {e}")
            _error = e

        self.alive = False
        self._arm.release_error_warn_changed_callback(self._error_warn_changed_callback)
        self._arm.release_state_changed_callback(self._state_changed_callback)
        if hasattr(self._arm, 'release_count_changed_callback'):
            self._arm.release_count_changed_callback(self._count_changed_callback)
        raise RuntimeError(f"suction_error: {_error}")
    
    def get_status(self,data=None):
        try:
            return {
                "alive": self.alive,
                "connected": self._arm.connected,
                "state": self._arm.state,
                "has_err_warn": self._arm.has_err_warn,
                "has_error": self._arm.has_error,
                "has_warn": self._arm.has_warn,
                "error_code": self._arm.error_code,
            }
        except Exception as e:
            self.pprint('MainException: {}'.format(e))
        self.alive = False
        self._arm.release_error_warn_changed_callback(self._error_warn_changed_callback)
        self._arm.release_state_changed_callback(self._state_changed_callback)
        if hasattr(self._arm, 'release_count_changed_callback'):
            self._arm.release_count_changed_callback(self._count_changed_callback)

        raise RuntimeError("get_robot_data failed")
    
    def get_current_position(self,data=None):
        try:
            joints = self.arm.get_servo_angle()[1]
            current_position = []
            current_position.append("CURRENT")
            current_position.append({
            "j1":round(joints[0]),
            "j2":round(joints[1]),
            "j3":round(joints[2]),
            "j4":round(joints[3]),
            "j5":round(joints[4]),
            "j6":round(joints[5])
            })
            return xarm_positions.find_closest_position(current_position)
        except Exception as e:
            self.pprint('MainException: {}'.format(e))
        self.alive = False
        self._arm.release_error_warn_changed_callback(self._error_warn_changed_callback)
        self._arm.release_state_changed_callback(self._state_changed_callback)
        if hasattr(self._arm, 'release_count_changed_callback'):
            self._arm.release_count_changed_callback(self._count_changed_callback)

        raise RuntimeError("get_position failed")
    
    def get_joints_position(self,data=None):
        try:
            joints = self.arm.get_servo_angle()[1]
            current_position = []
            current_position.append("CURRENT")
            current_position.append({
            "j1":round(joints[0]),
            "j2":round(joints[1]),
            "j3":round(joints[2]),
            "j4":round(joints[3]),
            "j5":round(joints[4]),
            "j6":round(joints[5])
            })
            return current_position
        except Exception as e:
            self.pprint('MainException: {}'.format(e))
        self.alive = False
        self._arm.release_error_warn_changed_callback(self._error_warn_changed_callback)
        self._arm.release_state_changed_callback(self._state_changed_callback)
        if hasattr(self._arm, 'release_count_changed_callback'):
            self._arm.release_count_changed_callback(self._count_changed_callback)

        raise RuntimeError("get_position failed")
