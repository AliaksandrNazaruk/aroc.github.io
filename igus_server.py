
import igus_modbus_lib
import json

import time
import threading
import logging
from http.server import BaseHTTPRequestHandler, HTTPServer
import arduino_controller.arduino_led_controller as als
import socket

s = None
import socket
import time

s = None

def igus_modbus_connect():
    """
    Устанавливает соединение с устройством через Modbus и выполняет инициализацию.
    """
    global s

    # Закрываем предыдущее соединение, если оно существует
    if s is not None:
        try:
            s.shutdown(socket.SHUT_RDWR)
            s.close()
            s = None
            time.sleep(3)
            print("Previous connection closed.")
        except Exception as e:
            print(f"Error while closing previous connection: {e}")

    try:
        # Создаем новый сокет
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(5)  # Устанавливаем тайм-аут для операций с сокетом
        # Подключаемся к устройству
        s.connect(("192.168.1.230", 502))
        print("Connected to Modbus device.")

    except socket.timeout:
        print("Connection timed out. Unable to connect to Modbus device.")
        s = None  # Сбрасываем объект соединения
    except socket.error as e:
        print(f"Socket error occurred: {e}")
        s = None  # Сбрасываем объект соединения
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        s = None  # Сбрасываем объект соединения

    # Проверяем успешность подключения
    if s is not None:
        print("Connection successfully established.")
        return True
    else:
        print("Failed to establish connection.")
        return False

igus_modbus_connect()

igus_is_busy = False

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

def send_command(command, with_led=False, value=None, velocity=None, stop_event=None):
    if command in IGUS_CONTROL_COMMANDS:
        if s is not None:
            if igus_modbus_lib.start_from_web_command(s, command,with_led, value, velocity, stop_event):
                if with_led:
                    als.send_command(1)
                return True
            else:        
                if with_led:
                    als.send_command(1)
    elif command in IGUS_STATUS_COMMANDS:
        if s is not None:
            result = igus_modbus_lib.get_from_web_command(s, command)
            if result:
                return result
    return False

stop_event = threading.Event()

def stop_motor():
    print("stop motor command")
    global jog_timer
    stop_event.set()
    jog_timer = 0
    jog_timer = None

def execute_command_async(command_name, with_led=False, value=None, velocity=None):
    global igus_is_busy
    igus_is_busy = True
    stop_event.clear()
    def worker(stop_event):
        global igus_is_busy
        print("Command: "+command_name+" is:")
        print(send_command(command_name,with_led, value, velocity, stop_event))
        igus_is_busy = False
    # Запускаем команду в отдельном потоке
    thread = threading.Thread(target=worker, args=(stop_event,))
    thread.start()

IGUS_CONTROL_COMMANDS = {
    "JOG_UP",
    "JOG_DOWN",
    "RESET",
    "WARN_RESET",
    "REFERENCE", 
    "ABS",
    "STOP"
}

IGUS_STATUS_COMMANDS = {
    "ACTUAL_POSITION",
    "REFERENCE_STATUS",
    "READY_STATUS"
}

jog_timer = None

def reset_timer(delay):
    global jog_timer
    if s is None:
        return
    if jog_timer:
        jog_timer.cancel()
    jog_timer = threading.Timer(delay, stop_motor)
    jog_timer.start()


class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def _set_headers(self, code=200, content_type="application/json"):
        """
        Установка заголовков ответа.
        """
        self.send_response(code)
        self.send_header("Content-type", content_type)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        
    def do_OPTIONS(self):
        """
        Обработка предварительных запросов OPTIONS.
        """
        self._set_headers()

    def igus_command_manager(self,post_data):
        global igus_is_busy
        global jog_timer
        try:
            json_data = json.loads(post_data)
            command_name = json_data.get("command")
            velocity = json_data.get("velocity")
            value = json_data.get("value")
            led = json_data.get("led")
            wait = json_data.get("wait")

            if value is not None:
                value = int(float(value)*1000)
            else:
                value = 0
            if velocity is not None:
                velocity = int(velocity) 
            else:
                velocity = 0
            if led is None:
                led = False
            if wait is None:
                wait = False

            if command_name in IGUS_CONTROL_COMMANDS:
                if (command_name == "STOP") :
                    stop_motor()
                    self._set_headers()
                    self.wfile.write(json.dumps("success").encode("utf-8"))
                    return

                if (command_name == "WARN_RESET") :
                    stop_motor()
                    send_command("RESET", False, value, velocity)
                    self._set_headers()
                    self.wfile.write(json.dumps("success").encode("utf-8"))
                    return

                else:
                    if not igus_is_busy:
                        if command_name == "RESET":
                            stop_motor()
                            igus_modbus_connect()
                            send_command("RESET", False, value, velocity)
                            time.sleep(5)
                            self._set_headers()
                            self.wfile.write(json.dumps("success").encode("utf-8"))
                            return
                        elif command_name == "ABS":
                            self._set_headers()
                            if wait:
                                if send_command(command_name, led, value, velocity):
                                    self.wfile.write(json.dumps("success").encode("utf-8"))
                                    return
                                else:
                                    self.wfile.write(json.dumps("failure").encode("utf-8"))
                                    return
                            else:
                                execute_command_async(command_name, led, value, velocity)
                                self.wfile.write(json.dumps("success").encode("utf-8"))
                                return
                        elif command_name == "JOG_UP" or command_name == "JOG_DOWN":
                            reset_timer(0.6)
                            execute_command_async(command_name, led, value, velocity)
                            self._set_headers()
                            self.wfile.write(json.dumps("success").encode("utf-8"))
                            return
                        else:
                            if wait:
                                if send_command(command_name, led, value, velocity):
                                    self._set_headers()
                                    self.wfile.write(json.dumps("success").encode("utf-8"))
                                    return
                            else: 
                                execute_command_async(command_name, led, value, velocity)
                                self._set_headers()
                                self.wfile.write(json.dumps("success").encode("utf-8"))
                                return
                    elif igus_is_busy:
                        if command_name == "JOG_UP" or command_name == "JOG_DOWN":
                            reset_timer(0.6)

            self._set_headers(400)
            self.wfile.write(b"Invalid command") 
        except Exception as e:
            self._set_headers(500)
            self.wfile.write(f"Error fetching position: {str(e)}".encode("utf-8"))
        
    def do_GET(self):

        if self.path == "/api/igus/get-actual-position":
            self._set_headers()
            result = send_command( "ACTUAL_POSITION", None)

            response_data = {
                "Position": result  # Changed to "Position" for consistency
            }
            self.wfile.write(json.dumps(response_data).encode("utf-8"))
            
        elif self.path == "/api/igus/get-reference-status":
            self._set_headers()
            result = send_command( "REFERENCE_STATUS", None)

            response_data = {
                "isActive": result
            }
            self.wfile.write(json.dumps(response_data).encode("utf-8"))

        elif self.path == "/api/igus/get-ready-status":
            self._set_headers()
            result = send_command( "READY_STATUS", None)

            response_data = {
                "isReady": result
            }
            self.wfile.write(json.dumps(response_data).encode("utf-8"))
            
        elif self.path == "/api/igus/igus-module-reset":
            self._set_headers()
            result = igus_modbus_connect()

            response_data = {
                "Position": result  # Changed to "Position" for consistency
            }
            self.wfile.write(json.dumps(response_data).encode("utf-8"))

        # Если запрос на тестовую страницу
        elif self.path == '/igus_test_page.html':
            self._set_headers(200, "text/html")
            try: 
                with open('igus_test_page.html', 'rb') as file:
                    self.wfile.write(file.read())
            except:
                self._set_headers(404)
                self.wfile.write(b"404 Not Found")
        else:
            self._set_headers(404)
            self.wfile.write(b"404 Not Found")


    def do_POST(self):
        if self.path == '/api/igus/send_command':
            try:
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)
                self.igus_command_manager(post_data)

            except Exception as e:
                self._set_headers(500)
                self.wfile.write(f"Error fetching position: {str(e)}".encode("utf-8"))
        else:
            self._set_headers(404)
            self.wfile.write(b"404 Not Found")

    def send_response_data(self, result):
        """
        Отправка данных обратно клиенту после выполнения команды
        """
        self._set_headers()
        self.wfile.write(json.dumps(result).encode("utf-8"))

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

if __name__ == "__main__":
    try:
        with HTTPServer(("", 8020), SimpleHTTPRequestHandler) as httpd:
            logging.info("Igus server on port 8020")
            httpd.serve_forever()
    except KeyboardInterrupt:
        logging.info("Server stopped by user.")
    except Exception as e:
        logging.critical(f"Critical error occurred: {e}")
