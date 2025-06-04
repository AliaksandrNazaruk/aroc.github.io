import requests
ip = "192.168.1.10"

def send_to_arduino(command):
    url = f"http://{ip}:8000/send"
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
    
