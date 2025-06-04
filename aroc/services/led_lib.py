import requests

from core.connection_config import web_server_ip, web_server_port

ip = web_server_ip

def send_to_arduino(command):
    url = f"http://{ip}:{web_server_port}/send"
    headers = {
        "Content-Type": "application/json",
    }
    data = {"command": command}
    
    try:
        response = requests.post(url, headers=headers, json=data, verify=False, timeout=2)
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
    
