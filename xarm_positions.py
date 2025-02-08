

import sys
import math
import time
import queue
import datetime
import random
import traceback
import threading
from xarm import version
from xarm.wrapper import XArmAPI


def calculate_difference(position1, position2):
    """
    Рассчитывает евклидово расстояние между двумя позициями.
    """
    return math.sqrt(
        (position1["j1"] - position2["j1"])**2 +
        (position1["j2"] - position2["j2"])**2 +
        (position1["j3"] - position2["j3"])**2 +
        (position1["j4"] - position2["j4"])**2 +
        (position1["j5"] - position2["j5"])**2 +
        (position1["j6"] - position2["j6"])**2
    )

def find_closest_position(current_position, saved_positions):
    """
    Находит ближайшую сохранённую позицию к текущей позиции.
    """

    for saved_position in saved_positions.items():
        difference = calculate_difference(current_position[1], saved_position[1])
        if difference == 0:
            return saved_position
    return current_position

poses = {
    "MEASURE_DESK" : {
        "j1": 57,
        "j2": 7,
        "j3": -49,
        "j4": -230,
        "j5": -21,
        "j6": 246
    },

    "BOX" : {
        "j1": 62,
        "j2": 26,
        "j3":-67,
        "j4": -57,
        "j5": 16,
        "j6": 84
    },

    "READY_STEP_1" : {
        "j1": 32,
        "j2": -90,
        "j3":-5,
        "j4":100,
        "j5": 26,
        "j6": -113
    },
    "READY_STEP_2" : {
        "j1": 32,
        "j2": -90,
        "j3":-5,
        "j4":172,
        "j5": 26,
        "j6": -173
    },
    "READY_SECTION_1" : {
        "j1": 119,
        "j2": -15,
        "j3": -20,
        "j4": 247,
        "j5": 115,
        "j6": -222
    },
    "READY_SECTION_2" : {
        "j1": 39,
        "j2": -78,
        "j3": -2,
        "j4": 185,
        "j5": 43,
        "j6": -190
    },
    "READY_SECTION_3" : {
        "j1": -28,
        "j2": -35,
        "j3": -21,
        "j4": 133,
        "j5": 88,
        "j6": -138
    },
    "READY_SECTION_4" : {
        "j1": -42,
        "j2": 4,
        "j3":-57,
        "j4": 125,
        "j5": 98,
        "j6": -131
    },
    "TRANSPORT_STEP_1" : {
        "j1": 32,
        "j2": -85,
        "j3":-5,
        "j4":100,
        "j5": 80,
        "j6": -113
    },

    "COLLISION" : {
        "j1": -56,
        "j2": -104,
        "j3":-7,
        "j4": 47,
        "j5": 120,
        "j6": -88
    },
    "TRANSPORT_STEP_2" : {
        "j1": 32,
        "j2": -85,
        "j3":-5,
        "j4":70,
        "j5": 165,
        "j6": -15
    }
}

def get_current_position():
    try:
        arm = XArmAPI('192.168.1.220', baud_checkset=False)
        joints = arm.get_servo_angle()[1]
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
        return find_closest_position(current_position, poses)
    finally:
        # Закрываем соединение с API, чтобы избежать зависания
        arm.disconnect()
