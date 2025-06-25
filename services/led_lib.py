import requests

from core.connection_config import web_server_ip, web_server_port
from core.logger import server_logger

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
        server_logger.log_event("info", f"API response: {response_data}")
        return response_data
    except requests.exceptions.RequestException as e:
        server_logger.log_event("error", f"Error performing POST request: {e}")
        return False
    except ValueError:
        server_logger.log_event("error", "Error: invalid JSON in response.")
        return False
    
