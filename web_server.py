
import json

import os
import arduino_controller.arduino_led_controller as als
import subprocess
import mimetypes
import threading

from xarm.wrapper import XArmAPI
import subprocess
from urllib.parse import parse_qs
from xarm_scripts import measure
from xarm_scripts import take_to_box
from xarm_scripts import get_depth_value
from xarm_scripts import take
from xarm_scripts import move_to_position
import os

from http.server import HTTPServer

from http.server import SimpleHTTPRequestHandler, HTTPServer


from main_scrypt import start_job_with_name
current_command = None
lift_running = False

print("Current working directory:", os.getcwd())
import igus_modbus_lib as wi
# Настройка порта и адреса
PORT = 8000
ADDRESS = "0.0.0.0"

job_done = False
thread_work = False

def start_job(decoded_data):
    global job_done
    global thread_work
    thread_work = True
    for key, values in decoded_data.items():
        name = str(key)  # Ключ в виде строки
        value = int(values[0])
        if value > 0:
            start_job_with_name(name)
    thread_work = False
    job_done = True  # Устанавливаем флаг


def xarm_command_operator(data):
    arm = None
    command = data["command"]
    try:

        if command == "move_tool_position":
            script_path = '/home/boris/web_server/xarm/xarm_scripts/move_tool_position.py'
            try: 
                args = [data["x"], data["y"], data["z"]]
                result = subprocess.run(
                    ["/bin/python", script_path, *map(str, args)],
                    capture_output=True,
                    text=True,
                    check=True
                )
                print("Output:", result.stdout)
                return True
            except subprocess.CalledProcessError as e:
                print("Error:", e.stderr)
                print("Subprocess failed with return code:", e.returncode)
                return False
        elif command == "get_depth_value":
            try:
                result = get_depth_value.get_depth()
                response_data = {
                    "depth":result
                }
                return response_data
            except:
                return False

        arm = XArmAPI('192.168.1.220', baud_checkset=False)
        if command == "move_to_position":
            script_path = '/home/boris/web_server/xarm/xarm_scripts/move_to_position.py'
            try: 
                robot_main = move_to_position.RobotMain(arm)
                result = robot_main.run(data["positions"])
                response_data = {
                    "result":result
                }
                return response_data
            except:
                return False
        if command == "take_to_box":
            try:
                robot_main = take_to_box.RobotMain(arm)
                result = robot_main.run()
                response_data = {
                    "result":result
                }
                return response_data
            except:
                return False
        elif command == "measure":
            try:
                robot_main = measure.RobotMain(arm)
                result = robot_main.run(data["correct_position"],data["move_to_measure_desk"])
                response_data = {
                    "x":int(result[0]), 
                    "y":int(result[1]), 
                    "w":int(result[2]), 
                    "h":int(result[3]), 
                    "depth":int(result[4]), 
                    "width":int(result[5]), 
                    "heigth":int(result[6])
                }
                return response_data
            except:
                return False
        elif command == "take":
            try:
                robot_main = take.RobotMain(arm)
                command = data["depth"]
                result = robot_main.run(command)
                response_data = {
                    "result":result
                }
                return response_data
            except:
                return False
        return False
    finally:
        if arm is not None:
            arm.disconnect()

class MyHTTPRequestHandler(SimpleHTTPRequestHandler):
    
    def do_GET(self):
        global job_done
        if self.path == "/job_status":
            # Отправляем JSON-ответ с состоянием работы
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"done": ' + (b"true" if job_done else b"false") + b'}')
            return
        if self.path == '/':
            file_name = 'login_page.html'
        elif self.path == '/control':
            file_name = 'index.html'
        else:
            file_name = self.path.lstrip('/')

        if os.path.exists(file_name) and os.path.isfile(file_name):  
            self.send_response(200)
            
            # Определяем Content-Type по расширению файла
            mime_type, _ = mimetypes.guess_type(file_name)
            if mime_type:
                self.send_header("Content-type", mime_type)
            else:
                self.send_header("Content-type", "application/octet-stream")
            
            self.end_headers()

            with open(file_name, 'rb') as file:
                self.wfile.write(file.read())
            return
        
        if self.path == '/status':
            response = {"status": "success", "message": "Serial connection check."}
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode())
            return

        # Если файл не найден, отдаем 404
        self.send_response(404)
        self.end_headers()
        self.wfile.write(b"404 Not Found")
        # Если файл не найден, отдаем 404
        self.send_response(404)
        self.end_headers()
        self.wfile.write(b"404 Not Found")


    def handle_static_files(self):
        file_path = self.path.strip('/')
        
        # Set default favicon if not provided
        if self.path == '/favicon.ico':
            file_path = 'static/favicon.ico'

        try:
            # Verify the file exists
            if not os.path.exists(file_path):
                raise FileNotFoundError

            # Determine content type
            if file_path.endswith('.css'):
                content_type = 'text/css'
            elif file_path.endswith('.js'):
                content_type = 'application/javascript'
            elif file_path.endswith('.ico'):
                content_type = 'image/x-icon'
            else:
                content_type = 'application/octet-stream'

            # Serve the file
            self.send_response(200)
            self.send_header('Content-type', content_type)
            self.end_headers()
            with open(file_path, 'rb') as file:
                self.wfile.write(file.read())
        
        except FileNotFoundError:
            # Log the missing file and return 404
            print(f"File not found: {file_path}")
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"404 Not Found")
        except BrokenPipeError:
            # Handle broken pipe error gracefully
            print("Broken pipe error while sending response.")

    def do_POST(self):
            global job_done
            global thread_work
            if self.path == '/send':
                # Обработка POST-запроса для отправки команды
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)

                try:
                    data = json.loads(post_data)
                    if "command" not in data:
                        raise ValueError("Invalid request. Command is required.")
                    command = data["command"]
                    result = als.send_command(command)
                    self.send_response(200)
                    self.end_headers()
                    self.wfile.write(json.dumps(result).encode())
                except (json.JSONDecodeError, ValueError) as e:
                    self.send_response(400)
                    self.end_headers()
                    self.wfile.write(json.dumps({"status": "error", "message": str(e)}).encode())
                except Exception as e:
                    self.send_response(500)
                    self.end_headers()
                    self.wfile.write(json.dumps({"status": "error", "message": "Internal server error"}).encode())
            elif self.path == '/api/echo':
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)
                try:
                    json_data = json.loads(post_data)
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    response = {"received": json_data}
                    self.wfile.write(json.dumps(response).encode('utf-8'))
                except json.JSONDecodeError:
                    self.send_response(400)
                    self.end_headers()
                    self.wfile.write(b"Invalid JSON")
            elif self.path == '/submit':
                content_length = int(self.headers.get('Content-Length', 0))
                post_data = self.rfile.read(content_length).decode('utf-8')
                
                # Разбираем form-urlencoded данные
                parsed_data = parse_qs(post_data)

                # Преобразуем ключи и значения из bytes в строки
                decoded_data = {key.decode() if isinstance(key, bytes) else key:
                                [value.decode() if isinstance(value, bytes) else value for value in values]
                                for key, values in parsed_data.items()}

                print("Полученные данные:", decoded_data)  # Логируем в консоль

                # Отправляем 302 Redirect
                self.send_response(302)
                self.send_header('Location', 'http://192.168.1.10:8000/new_waiting_one_pick_ready.html')
                self.end_headers()
                # Запускаем долгую функцию в отдельном потоке
                # start_job(decoded_data)
                if thread_work == False:
                    job_done = False
                    thread = threading.Thread(target=start_job, args=(decoded_data,), daemon=True)
                    thread.start()

                # Отправляем 302 Redirect
                # self.send_response(302)
                # self.send_header('Location', 'http://192.168.1.10:8000/cockpit_one_pick_2.html')
                # self.end_headers()
            elif self.path == '/start/xarm_script':
                content_length = int(self.headers['Content-Length'])
                try:
                    post_data = self.rfile.read(content_length)
                    data = json.loads(post_data)

                    result = xarm_command_operator(data)
                    if result == False:
                        self.send_response(400)
                        self.end_headers()
                    else:
                        self.send_response(200)
                        self.end_headers()
                        self.wfile.write(json.dumps(result).encode("utf-8"))

                except Exception as e:
                    self.send_response(500)
                    self.end_headers()
                    self.wfile.write(json.dumps({"status": "error", "message": "Internal server error"}).encode())
            else:
                self.send_response(404)
                self.end_headers()
                self.wfile.write(b"404 Not Found")

    def do_PUT(self):

        if self.path == '/api/update':
            content_length = int(self.headers['Content-Length'])
            put_data = self.rfile.read(content_length)
            try:
                json_data = json.loads(put_data)
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                response = {"updated": json_data}
                self.wfile.write(json.dumps(response).encode('utf-8'))
            except json.JSONDecodeError:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b"Invalid JSON")
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"404 Not Found")

if __name__ == '__main__':
    with HTTPServer((ADDRESS, PORT), MyHTTPRequestHandler) as httpd:
        print(f"Serving on {ADDRESS}:{PORT}")
        httpd.serve_forever()