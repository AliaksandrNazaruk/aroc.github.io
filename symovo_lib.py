import requests
requests.packages.urllib3.disable_warnings()
import igus_lib

# IP-адрес сервера
ip = "192.168.1.100"

# Функция для выполнения GET-запроса
def req(url):
    headers = {"Content-Type": "application/json"}
    try:
        response = requests.get(url=url, headers=headers, verify=False, timeout=10)  # Добавлен тайм-аут
        response.raise_for_status()  # Проверка на ошибки HTTP
        response_data = response.json()  # Попытка декодировать JSON
        print("Status Code:", response.status_code)
        return response_data
    except requests.exceptions.RequestException as e:
        print("Ошибка при выполнении GET-запроса:", e)
        return None
    except ValueError:
        print("Ошибка: некорректный JSON в ответе.")
        return None

def get_job_from_name(list,name):
    for job in list:
        if name == job['name']:
            return job
import requests
import math

def get_robot_position():
    """Получает текущие координаты робота."""
    url = "https://"+ip+"/v0/agv/15/pose"
    response = requests.get(url, verify=False)  # verify=False отключает проверку SSL
    data = response.json()
    return data["pose"]["x"], data["pose"]["y"]

def get_stations():
    """Получает список станций с их координатами."""
    url = "https://"+ip+"/v0/station"
    response = requests.get(url, verify=False)
    return response.json()

def find_nearest_station():
    """Определяет ближайшую станцию к роботу."""
    robot_x, robot_y = get_robot_position()
    stations = get_stations()
    nearest_station = "Unknown"
    nearest_station = None
    min_distance = 0.05

    for station in stations:
        station_x = station["pose"]["x"]
        station_y = station["pose"]["y"]

        # Вычисляем евклидово расстояние
        distance = math.sqrt((robot_x - station_x) ** 2 + (robot_y - station_y) ** 2)

        if distance < min_distance:
            min_distance = distance
            nearest_station = station["name"]

    return nearest_station


def create_transport_from_job(job):
    job_id = job.get('id') 
    if not job_id:
        print("Ошибка: задание не содержит 'id'.")
        return False

    headers = {
        "Content-Type": "application/json",
    }
    put_create_transport_from_job = f"https://{ip}/v0/transport/create_from_job/{job_id}"

    try:
        response = requests.put(put_create_transport_from_job, headers=headers, verify=False, timeout=30)
        response.raise_for_status()
        response_data = response.json()
        print("Ответ API:", response_data)
        transport_id = response_data.get("transport_id")
        print("Созданный transport_id:", transport_id)
        return transport_id
    except requests.exceptions.RequestException as e:
        print("Ошибка при выполнении PUT-запроса:", e)
        return False
    except ValueError:
        print("Ошибка: некорректный JSON в ответе.")
        return False
    
def agv_on_charging():
    try:
        url = "https://"+ip+"/v0/agv/15"
        response = requests.get(url, verify=False)  # verify=False отключает проверку SSL
        data = response.json()['state_flags']
        if data['reed_closed'] == True:
            return True
        return False
    except:
        return False

def go_to_position(name,reconfig=False,wait=False):
    jobs = req(f"https://{ip}/v0/job")
    current_station = find_nearest_station()
    if reconfig:
        if ("GoTo"+current_station)!=name:
            igus_lib.go_to_position(0,2000,reconfig,wait)
    
    if name == "GoToRack1":
        create_transport_from_job(get_job_from_name(jobs,'GoToRack1'))
    if name == "GoToRack2":
        create_transport_from_job(get_job_from_name(jobs,'GoToRack2'))
    if name == "GoToPresentation":
        create_transport_from_job(get_job_from_name(jobs,'GoToPresentation'))
    if name == "GoToLastPoint":
        create_transport_from_job(get_job_from_name(jobs,'GoToLastPoint'))