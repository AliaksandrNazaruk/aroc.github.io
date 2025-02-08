import requests
# Отключение предупреждений о проверке SSL-сертификатов
requests.packages.urllib3.disable_warnings()
import xarm_positions

# IP-адрес сервера
ip = "192.168.1.10"


def send_to_webserver(command, path="", _data=None):
    url = f"http://{ip}:8000" + path
    headers = {
        "Content-Type": "application/json",
    }
    
    data = {"command": command}

    if _data is not None:
        if isinstance(_data, dict):  # Если _data - словарь
            data.update(_data)
        elif isinstance(_data, list):  # Если _data - список, вложим в data
            data["positions"] = _data
        else:
            print("Ошибка: Неверный формат _data")
            return False

    try:
        response = requests.post(url, headers=headers, json=data, verify=False, timeout=100)
        response.raise_for_status()
        print("Ответ API:", response.status_code)
        return True
    except requests.exceptions.RequestException as e:
        print("Ошибка при выполнении POST-запроса:", e)
        return False
    except ValueError:
        print("Ошибка: некорректный JSON в ответе.")
        return False
    

def go_to_position(data1=None, data2=None, data3=None, data4=None, angle_speed=20): 
    _data = {"angle_speed": angle_speed}
    
    # Формируем список только из непустых data
    positions = [data for data in [data1, data2, data3, data4] if data is not None]
    
    # Добавляем angle_speed в каждый словарь
    json_data = [{**data, **_data} for data in positions]

    return send_to_webserver("move_to_position", "/start/xarm_script", _data=json_data)