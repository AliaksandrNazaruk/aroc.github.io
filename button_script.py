from gpiozero import Button
from time import time, sleep
import os

button = Button(14)
def short_press():
    os.system("sudo systemctl restart my_robot.service")

def long_press():
    os.system("sudo systemctl stop my_robot.service")


while True:
    try:
        button.wait_for_press()
        press_time = time()

        button.wait_for_release()
        release_time = time()

        hold_duration = release_time - press_time

        if hold_duration>5:
            long_press()
        elif hold_duration >= 1:
            short_press()

    except:
        continue
