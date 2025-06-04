import requests
import time
import threading
from datetime import datetime
import math
requests.packages.urllib3.disable_warnings()
# import services.igus_lib as igus_lib
from core.configuration import symovo_car_ip, symovo_car_number
def get_job_from_name(list,name):
    for job in list:
        if name == job['name']:
            return job
        
class AgvClient:
    def __init__(self, ip="", robot_number=""):
        self.ip = ip
        self.robot_number = robot_number

        # Поля, которые будем обновлять при каждом успешном запросе
        self.id = None
        self.name = None
        self.pose_x = None
        self.pose_y = None
        self.pose_theta = None
        self.pose_map_id = None
        self.velocity_x = None
        self.velocity_y = None
        self.velocity_theta = None
        self.state = None
        self.battery_level = None
        self.state_flags = {}
        self.robot_ip = None
        self.replication_port = None
        self.api_port = None
        self.iot_port = None
        self.last_seen = None
        self.enabled = None
        self.last_update = None
        self.attributes = {}
        self.planned_path_edges = []

        # Дополнительные переменные
        self.last_update_time = None  # Время последнего опроса
        self.online = False           # Статус подключения

        # Для фонового опроса
        self._stop_event = threading.Event()
        self._polling_thread = None

    def _get_robot_url(self):
        """Генерирует URL для запроса данных AGV."""
        return f"https://{self.ip}/v0/agv/{self.robot_number}"
    
    def _get_transport_url(self):
        """Генерирует URL для запроса данных AGV."""
        return f"https://{self.ip}/v0/transport"
    
    def _get_job_url(self):
        """Генерирует URL для запроса данных AGV."""
        return f"https://{self.ip}/v0/job"
    
    def _get_stations_url(self):
        """Генерирует URL для запроса данных AGV."""
        return f"https://{self.ip}/v0/station"
    
    def poll(self):
        """
        Опрос AGV (GET-запрос).
        При удачном ответе обновляет все поля класса.
        При ошибке выставляет self.online = False.
        """
        url = self._get_robot_url()
        try:
            response = requests.get(url, verify=False, timeout=10)
            response.raise_for_status()
            data = response.json()

            # Удачный запрос
            self.online = True
            self.last_update_time = datetime.now()

            # Обновляем основные поля
            self.id = data.get('id')
            self.name = data.get('name')

            pose = data.get('pose', {})
            self.pose_x = pose.get('x')
            self.pose_y = pose.get('y')
            self.pose_theta = pose.get('theta')
            self.pose_map_id = pose.get('map_id')

            velocity = data.get('velocity', {})
            if velocity is not None:
                self.velocity_x = velocity.get('x')
                self.velocity_y = velocity.get('y')
                self.velocity_theta = velocity.get('theta')

            self.state = data.get('state')
            self.battery_level = data.get('battery_level')
            self.state_flags = data.get('state_flags', {})

            self.robot_ip = data.get('ip')
            self.replication_port = data.get('replication_port')
            self.api_port = data.get('api_port')
            self.iot_port = data.get('iot_port')
            self.last_seen = data.get('last_seen')
            self.enabled = data.get('enabled')
            self.last_update = data.get('last_update')
            self.attributes = data.get('attributes', {})
            self.planned_path_edges = data.get('planned_path_edges', [])

        except requests.exceptions.RequestException as e:
            # Ошибка при запросе
            print(f"Ошибка при опросе AGV: {e}")
            self.online = False
        except ValueError:
            # Некорректный JSON
            print("Ошибка: некорректный JSON в ответе.")
            self.online = False

    def start_polling(self, interval=5):
        """
        Запускает фоновый поток, который каждые interval секунд 
        вызывает метод poll() для обновления данных о роботе.
        """

        def polling_loop():
            while not self._stop_event.is_set():
                self.poll()
                time.sleep(interval)

        self._stop_event.clear()
        self._polling_thread = threading.Thread(target=polling_loop, daemon=True)
        self._polling_thread.start()

    def stop_polling(self):
        """Останавливает фоновый опрос."""
        if self._stop_event:
            self._stop_event.set()
        if self._polling_thread:
            self._polling_thread.join()

    def get_jobs(self):
        url = self._get_job_url()
        try:
            response = requests.get(url, verify=False, timeout=10)
            response.raise_for_status()
            data = response.json()
            return data
        except requests.exceptions.RequestException as e:
            # Ошибка при запросе
            print(f"Ошибка при опросе AGV: {e}")
            self.online = False
            return False
        except ValueError:
            # Некорректный JSON
            print("Ошибка: некорректный JSON в ответе.")
            self.online = False
            return False

    def create_transport_from_job(self, job):
        headers = {
            "Content-Type": "application/json",
        }
        job_id = job.get('id') 
        if not job_id:
            print("Ошибка: задание не содержит 'id'.")
            return False
        url = self._get_transport_url()
        put_create_transport_from_job = f"{url}/create_from_job/{job_id}"

        try:
            response = requests.put(put_create_transport_from_job, headers=headers, verify=False, timeout=30)
            response.raise_for_status()
            data = response.json()
            return data
        except requests.exceptions.RequestException as e:
            print("Ошибка при выполнении PUT-запроса:", e)
            return False
        except ValueError:
            print("Ошибка: некорректный JSON в ответе.")
            return False

    def get_robot_position(self):
        """Получает текущие координаты робота."""
        url = self._get_robot_url() +"/pose"
        try:
            response = requests.get(url, verify=False, timeout=10)
            response.raise_for_status()
            data = response.json()
            return data["pose"]["x"], data["pose"]["y"]
        except requests.exceptions.RequestException as e:
            # Ошибка при запросе
            print(f"Ошибка при опросе AGV: {e}")
            self.online = False
            return False
        except ValueError:
            # Некорректный JSON
            print("Ошибка: некорректный JSON в ответе.")
            self.online = False
            return False

    def get_stations(self):
        """Получает список станций с их координатами."""
        url = self._get_stations_url()
        try:
            response = requests.get(url, verify=False, timeout=10)
            return response.json()
        except requests.exceptions.RequestException as e:
            # Ошибка при запросе
            print(f"Ошибка при опросе AGV: {e}")
            self.online = False
            return False
        except ValueError:
            # Некорректный JSON
            print("Ошибка: некорректный JSON в ответе.")
            self.online = False
            return False
        
    def find_nearest_station(self):
        """
        Определяет ближайшую станцию к роботу.
        Возвращает полный словарь данных о ближайшей станции,
        дополнительно добавляя ключ "distance" с вычисленным расстоянием.
        """
        robot_x, robot_y = self.get_robot_position()
        stations = self.get_stations()
        
        if not stations:
            return None  # Если станций нет, сразу возвращаем None

        nearest_station = None
        min_distance = float('inf')

        for station in stations:
            station_x = station["pose"]["x"]
            station_y = station["pose"]["y"]
            
            # Вычисляем евклидово расстояние
            distance = math.sqrt((robot_x - station_x)**2 + (robot_y - station_y)**2)

            if distance < min_distance:
                min_distance = distance
                nearest_station = station

        # Добавим в результат расстояние (при необходимости)
        if nearest_station is not None:
            nearest_station = dict(nearest_station)  # Скопируем, если не хотим менять оригинал
            nearest_station["distance"] = min_distance

        return nearest_station
    
    def go_to_position(self, name, reconfig=False, wait=False):
        try:
            jobs = self.get_jobs()
            nearest_station = self.find_nearest_station()
            current_station = None

            # If we successfully determined the nearest station and it is
            # essentially the same as the requested one (within 5 cm), we can
            # skip creating a new job.
            if nearest_station and nearest_station.get("distance", float("inf")) < 0.05:
                current_station = nearest_station

            if current_station is not None:
                if current_station.get("name") == name:
                    return True
            # if reconfig:
            #     igus_lib.go_to_position(0, 4000, reconfig, True)
            if self.create_transport_from_job(get_job_from_name(jobs, name)) != False:
                return True
            return False

        except Exception as e:
            return e



# ================================
# Пример использования:
# ================================

if __name__ == "__main__":
    client = AgvClient(ip=symovo_car_ip, robot_number=symovo_car_number)
    client.start_polling(interval=10)
    print(client.go_to_position("Test",True,True))