import requests
# Отключение предупреждений о проверке SSL-сертификатов
requests.packages.urllib3.disable_warnings()
import xarm_positions
import robot_lib
import time
# IP-адрес сервера
ip = "192.168.1.10"

def get_from_igus(path="send_command", wait=False):
    url = f"http://{ip}:8020/api/igus/"+path
    headers = {
        "Content-Type": "application/json",
    }
    data = {
        "wait":wait
    }
    
    try:
        response = requests.get(url, headers=headers, json=data, verify=False, timeout=50)
        response.raise_for_status()
        response_data = response.json()
        print("Ответ API:", response_data)
        return response_data
    except requests.exceptions.RequestException as e:
        print("Ошибка при выполнении POST-запроса:", e)
        return False
    except ValueError:
        print("Ошибка: некорректный JSON в ответе.")
        return False
    
def send_to_igus(command, path="send_command", value=0, velocity=0, wait=False):
    url = f"http://{ip}:8020/api/igus/"+path
    headers = {
        "Content-Type": "application/json",
    }
    data = {
        "command": command,
        "value": value,
        "velocity": velocity,
        "wait":wait
    }
    
    try:

        response = requests.post(url, headers=headers, json=data, verify=False, timeout=50)
        response.raise_for_status()

        response_data = response.json()
        print("Ответ API:", response_data)
        return response_data
    except requests.exceptions.RequestException as e:
        print("Ошибка при выполнении POST-запроса:", e)
        return False
    except ValueError:
        print("Ошибка: некорректный JSON в ответе.")
        return False


def get_ready_status(wait):
     try:
        result = get_from_igus(path = 'get-ready-status',wait=wait)
        if result['isReady'] == True:
            return True
        return False
     except:
        return False



def error_clear(wait):
    try:
        result = send_to_igus("RESET", wait=wait)
        if result == 'success':
            return True
        return False
    except:
         return False
    
def reference(wait):
    try:
        result = send_to_igus("REFERENCE", wait=wait)
        if result == 'success':
            return True
        return False
    except:
         return False
    
def set_ready_status(wait):
    try:
        error_clear(wait)
        if get_ready_status(True) != True: 
            reference(wait)
        else:
            return True
        if get_ready_status(True) != True: 
                return False
        return True
    except:
        return False
    

def reconfig_func():
    try:
        pose = xarm_positions.get_current_position()
        if pose[0]!="TRANSPORT_STEP_2":
            if robot_lib.go_to_position(xarm_positions.poses["TRANSPORT_STEP_1"], xarm_positions.poses["TRANSPORT_STEP_2"], angle_speed=40):
                return True
        else:
            return True
        return False
    except:
        return False
    
def go_to(value,velocity,reconfig,wait):
    try:
        if reconfig:
            if reconfig_func():
                result = send_to_igus("ABS", value=value, velocity=velocity, wait=wait)
                if result != False:
                    return True
        else:
            result = send_to_igus("ABS", value=value, velocity=velocity, wait=wait)
            if result != False:
                return True
        return False
    except:
        return False
def go_to_position(value, velocity, reconfig=False,wait=False):
    try:
        if get_ready_status(True):
            return go_to(value,velocity,reconfig,wait)
        else:
            if set_ready_status(True):
                return go_to(value,velocity,reconfig,wait)
        return False
    except:
        return False
    