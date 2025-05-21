import os
import json
import threading
import sqlite3
import asyncio
import sys
import io
from fastapi import Query
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import websockets
from configuration import symovo_car_ip,symovo_car_number, igus_motor_ip, igus_motor_port
from typing import Dict, Any, Optional, List
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime
from collections import deque

# импорт из ваших модулей
import arduino_controller.arduino_led_controller as als
from high_level.robot_scrypts import start_job_with_name, script_operator
from low_level.xarm_scripts.xarm_command_operator import xarm_command_operator
from low_level.igus_scripts.igus_command_operator import igus_command_operator
import middle_level.symovo_lib as symovo_lib
import middle_level.igus_lib as igus_lib

DB_PATH = "database.db"

class ServerLogger:
    def __init__(self, max_log_entries: int = 10000):
        self.max_log_entries = max_log_entries
        self.log_history = deque(maxlen=max_log_entries)
        self.original_stdout = sys.stdout
        self.original_stderr = sys.stderr
        self.setup_logging()
        
    def setup_logging(self):
        # Настройка файлового логирования
        file_handler = RotatingFileHandler(
            'server_logs.log',
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        ))
        
        # Настройка консольного логирования
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        ))
        
        # Настройка основного логгера
        self.logger = logging.getLogger('server_logger')
        self.logger.setLevel(logging.DEBUG)
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        
        # Перехват stdout и stderr
        sys.stdout = self.StreamLogger(self, 'stdout')
        sys.stderr = self.StreamLogger(self, 'stderr')
        
    class StreamLogger(io.TextIOBase):
        def __init__(self, parent, stream_type):
            self.parent = parent
            self.stream_type = stream_type
            self.buffer = []
            
        def write(self, text):
            if text.strip():  # Игнорируем пустые строки
                timestamp = datetime.now().isoformat()
                log_entry = {
                    'timestamp': timestamp,
                    'type': self.stream_type,
                    'message': text.strip()
                }
                self.parent.log_history.append(log_entry)
                
                # Также записываем в оригинальный поток
                if self.stream_type == 'stdout':
                    self.parent.original_stdout.write(text)
                else:
                    self.parent.original_stderr.write(text)
                    
        def flush(self):
            if self.stream_type == 'stdout':
                self.parent.original_stdout.flush()
            else:
                self.parent.original_stderr.flush()
                
    def log_event(self, level: str, message: str, data: Dict = None):
        """Логирование события с уровнем важности"""
        timestamp = datetime.now().isoformat()
        log_entry = {
            'timestamp': timestamp,
            'level': level,
            'message': message,
            'data': data
        }
        
        self.log_history.append(log_entry)
        
        if level == 'debug':
            self.logger.debug(message, extra={'data': data})
        elif level == 'info':
            self.logger.info(message, extra={'data': data})
        elif level == 'warning':
            self.logger.warning(message, extra={'data': data})
        elif level == 'error':
            self.logger.error(message, extra={'data': data})
        elif level == 'critical':
            self.logger.critical(message, extra={'data': data})
            
    def get_log_history(self, limit: int = None) -> List[Dict]:
        """Получение истории логов с опциональным ограничением"""
        if limit is None:
            return list(self.log_history)
        return list(self.log_history)[-limit:]
        
    def clear_logs(self):
        """Очистка истории логов"""
        self.log_history.clear()

server_logger = ServerLogger()

job_done = False
thread_work = False
script_stop_event = threading.Event()  
thread = None  
script_statuses = ["WORKING", "FINISHED", "NOT_RUNING", "STOPPED", "FAILED"]
script_status = script_statuses[3]

symovo_car = symovo_lib.AgvClient(ip=symovo_car_ip, robot_number=symovo_car_number)
symovo_car.start_polling(interval=10)

igus_motor = igus_lib.IgusClient(ip=igus_motor_ip, port=igus_motor_port)
igus_motor.start_polling(interval=3)

logger = logging.getLogger(__name__)

def init_db():
    """Создаём (если нет) таблицу regals, где храним объекты в JSON."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS regals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

def init_trajectory_table():
    """
    Создаём (если нет) таблицу trajectory для хранения конфигурации траектории.
    Таблица будет содержать единственную запись с id = 1.
    """
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS trajectory (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            data TEXT NOT NULL
        )
    """)
    # Если запись не существует, вставляем значение по умолчанию
    c.execute("SELECT COUNT(*) FROM trajectory")
    if c.fetchone()[0] == 0:
        default_config = json.dumps({
            "prefix": {"active": False, "posX": 0, "posY": 0, "posZ": 0, "speed": 100},
            "postfix": {"active": False, "posX": 0, "posY": 0, "posZ": 0, "speed": 100},
            "gripper": {"active": False},
            "return": {"active": False}
        })
        c.execute("INSERT INTO trajectory (id, data) VALUES (1, ?)", (default_config,))
    conn.commit()
    conn.close()

# ----------------- БИЗНЕС-ЛОГИКА -----------------
def start_job(_data):
    global job_done
    global thread_work
    thread_work = True
    start_job_with_name(_data)
    thread_work = False
    job_done = True  # Устанавливаем флаг

def start_script(arg):
    global thread_work, script_status, script_stop_event
    script_stop_event.clear()  # Сбрасываем флаг перед стартом
    script_status = script_statuses[0]
    thread_work = True
    result = script_operator(script_stop_event,arg)
    if script_stop_event.is_set():
        script_status = script_statuses[3]
    else:
        if result:
            script_status = script_statuses[1]
        else:
            script_status = script_statuses[4]
    thread_work = False

def stop_script():
    global script_status, thread_work, script_stop_event
    if thread_work == False:
        script_status=script_statuses[2]
    else:
        script_stop_event.set() 
    
# --------------- СОЗДАЁМ ПРИЛОЖЕНИЕ FASTAPI ---------------
app = FastAPI()

# ----------------------- STATIC FILES -----------------------
app.mount("/static", StaticFiles(directory="static"), name="static")
    
# ------------------- HTTP РОУТЫ (GET/POST и т.п.) -------------------
@app.on_event("startup")
def on_startup():
    init_db()
    init_trajectory_table()
    print("Database and trajectory table initialized (if not exists).")

@app.get("/")
def get_root():
    filename = "index.html"
    if not os.path.exists(filename):
        return JSONResponse(content={"error": "File not found"}, status_code=404)
    return FileResponse(filename)

@app.get("/control")
def get_control_page():
    filename = "index.html"
    if not os.path.exists(filename):
        return JSONResponse(content={"error": "File not found"}, status_code=404)
    return FileResponse(filename)

@app.get("/job_status")
def get_job_status():
    return {"done": job_done}

@app.get("/script_status")
def get_script_status():
    return {"status": script_status}

@app.get("/stop_script")
def stop_script_endpoint():
    stop_script()
    return {"status": script_status}

@app.get("/status")
def check_status():
    return {"status": "success", "message": "Serial connection check."}

# ------------------- ПРОЧИЕ POST МЕТОДЫ -------------------

@app.post("/api/arduino/send")
def send_command(data: dict):
    """Пример POST /send: отправка команды Arduino."""
    if "command" not in data:
        raise HTTPException(status_code=400, detail="Invalid request. 'command' is required.")
    command = data["command"]
    try:
        result = als.send_command(command)  # ваша функция
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
@app.post("/echo")
def echo(data: dict):
    """Отправляем назад что получили."""
    return {"received": data}
@app.post("/submit")
def handle_submit(data: dict):
    """
    Пример POST /submit, для запуска некой «job».
    """
    global job_done, thread_work, thread
    # data = json.loads(post_data) -- FastAPI сам уже распарсил JSON
    try:
        if not thread_work:
            job_done = False
            thread = threading.Thread(target=start_job, args=(data,), daemon=True)
            thread.start()
        return {"status": "ok", "message": "Operator confirmed movement"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
@app.post("/start/xarm_script")
def start_xarm_script(data: dict):
    """Пример: запускаем xarm_command_operator."""
    try:
        result = xarm_command_operator(data)
        if type(result) == Exception:
            detail=f'XARM Operator: {type(result).__name__}: {result}'
            raise HTTPException(status_code=400, detail=detail)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
@app.post("/start/igus_script")
def start_igus_script(data: dict):
    """
    Выполняет команду для управления Igus мотором.
    
    Args:
        data: Dictionary containing:
            - command: Тип команды (reference, get_robot_data, move_to_position)
            - position: Целевая позиция (для move_to_position)
            - velocity: Скорость (для move_to_position)
            - acceleration: Ускорение (для move_to_position)
            - depth: Глубина (для get_robot_data)
            
    Returns:
        Dict[str, Any]: Результат выполнения команды
        
    Raises:
        HTTPException: При ошибках выполнения команды
    """
    try:
        # Валидация входных данных
        if not isinstance(data, dict):
            raise HTTPException(
                status_code=400,
                detail="Invalid request: data must be a dictionary"
            )
            
        if "command" not in data:
            raise HTTPException(
                status_code=400,
                detail="Invalid request: 'command' is required"
            )
            
        # Проверка параметров для move_to_position
        if data["command"] == "move_to_position":
            required_params = ["position", "velocity", "acceleration"]
            for param in required_params:
                if param not in data:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Missing required parameter: {param}"
                    )
                if not isinstance(data[param], (int, float)):
                    raise HTTPException(
                        status_code=400,
                        detail=f"Parameter {param} must be numeric"
                    )
        
        # Логирование начала выполнения команды
        logger.info(f"Starting Igus command: {data['command']}")
        
        # Выполнение команды
        result = igus_command_operator(data)
        
        # Проверка результата
        if isinstance(result, Exception):
            logger.error(f"Igus Operator error: {str(result)}")
            raise HTTPException(
                status_code=500,
                detail=f"Igus Operator error: {str(result)}"
            )
            
        if not isinstance(result, dict):
            logger.error("Invalid response format from Igus operator")
            raise HTTPException(
                status_code=500,
                detail="Invalid response format from Igus operator"
            )
            
        # Логирование успешного выполнения
        logger.info(f"Igus command completed successfully: {data['command']}")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in Igus script: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )
@app.post("/run_script")
def run_script(data: dict):
    print(data)
    global thread_work, thread_status, thread, script_status

    try:
        if "command" not in data:
            raise HTTPException(status_code=400, detail="No 'command' in JSON")
        
        if not thread_work:
            # Запускаем скрипт в отдельном потоке
            thread = threading.Thread(target=start_script, args=(data["command"],), daemon=True)
            thread.start()
            return True
        else:
            script_status = script_statuses[4]  # FAILED
            raise HTTPException(status_code=500, detail="Thread is not available")
    except Exception as e:
        script_status = script_statuses[4]
        raise HTTPException(status_code=500, detail=f"Internal error: {e}")
@app.post("/stop_script")
def stop_script_endpoint_post():
    """POST вариант остановки скрипта."""
    stop_script()
    return {"status": script_status}

# ------------------- WEBSOCKET МАРШРУТЫ -------------------
async def forward_messages_fastapi_to_websockets(src_ws: WebSocket, dst_ws: websockets.WebSocketClientProtocol):
    """
    Читает сообщения из WebSocket FastAPI (src_ws) и пишет в websockets (dst_ws).
    Может быть текст или бинарные данные.
    """
    try:
        while True:
            # универсальный способ
            message = await src_ws.receive()
            # print(message)
            # message — словарь вида {"type": "websocket.receive", "text": "..."} или {"bytes": b"..."}
            if "text" in message and message["text"] is not None:
                # Текстовое сообщение
                text_data = message["text"]
                print("text_data")
                await dst_ws.send(text_data)
            elif "bytes" in message and message["bytes"] is not None:
                # Бинарное сообщение
                bin_data = message["bytes"]
                print("bin_data")
                await dst_ws.send_bytes(bin_data)
            else:
                print("unknown_type")
                # ping/pong/close?
                break
    except WebSocketDisconnect:
        pass
    except Exception as e:
        print("Error (fastapi->websockets):", e)
async def forward_messages_websockets_to_fastapi(src_ws, dst_ws):
    async for msg in src_ws:
        # Допустим, msg — это строка с Base64
        if isinstance(msg, str):
            # print(f"[->Proxy] Received text msg, length={len(msg)}")
            # Можно вывести первые 50 символов, чтобы не засорять лог:
            # print(f"   chunk={msg[:50]}...")
            await dst_ws.send_text(msg)
        else:
            # print(f"[->Proxy] Received BINARY msg, length={len(msg)}")
            await dst_ws.send_bytes(msg)
@app.websocket("/depth")
async def depth_ws(websocket: WebSocket):
    """При запросе ws://host:port/depth — коннектимся к ws://localhost:9999 и проксируем."""
    await websocket.accept()
    try:
        async with websockets.connect("ws://192.168.1.55:9999") as depth_ws:
            # Запускаем корутины пересылки
            print("Connected to camera on 9999")  # <-- добавить
            await asyncio.gather(
                forward_messages_fastapi_to_websockets(websocket, depth_ws),
                forward_messages_websockets_to_fastapi(depth_ws, websocket)
            )
    except WebSocketDisconnect:
        # клиент (браузер) закрыл вкладку
        pass
    except Exception as e:
        print("Some other error: ", e)
    finally:
        # Если всё ещё открыто, можно закрыть
        if not websocket.client_state.name == "DISCONNECTED":
            await websocket.close()
@app.websocket("/depth_query")
async def color_ws(websocket: WebSocket):
    """При запросе ws://host:port/color — коннектимся к ws://localhost:9998 и проксируем."""
    await websocket.accept()
    try:
        async with websockets.connect("ws://192.168.1.55:10000") as color_ws:

            await asyncio.gather(
                forward_messages_fastapi_to_websockets(websocket, color_ws),
                forward_messages_websockets_to_fastapi(color_ws, websocket)
            )
    except WebSocketDisconnect:
        # клиент (браузер) закрыл вкладку
        pass
    except Exception as e:
        print("Some other error: ", e)
    finally:
        # Если всё ещё открыто, можно закрыть
        if not websocket.client_state.name == "DISCONNECTED":
            await websocket.close()
@app.websocket("/color")
async def color_ws(websocket: WebSocket):
    """При запросе ws://host:port/color — коннектимся к ws://localhost:9998 и проксируем."""
    await websocket.accept()
    try:
        async with websockets.connect("ws://192.168.1.55:9998") as color_ws:
            print("Connected to camera on 9998")  # <-- добавить
            await asyncio.gather(
                forward_messages_fastapi_to_websockets(websocket, color_ws),
                forward_messages_websockets_to_fastapi(color_ws, websocket)
            )
    except WebSocketDisconnect:
        # клиент (браузер) закрыл вкладку
        pass
    except Exception as e:
        print("Some other error: ", e)
    finally:
        # Если всё ещё открыто, можно закрыть
        if not websocket.client_state.name == "DISCONNECTED":
            await websocket.close()
@app.websocket("/camera2")
async def color_ws(websocket: WebSocket):
    """При запросе ws://host:port/color — коннектимся к ws://localhost:9997 и проксируем."""
    await websocket.accept()
    try:
        async with websockets.connect("ws://localhost:9998") as color_ws:
            print("Connected to camera on 9998")  # <-- добавить
            await asyncio.gather(
                forward_messages_fastapi_to_websockets(websocket, color_ws),
                forward_messages_websockets_to_fastapi(color_ws, websocket)
            )
    except WebSocketDisconnect:
        # клиент (браузер) закрыл вкладку
        pass
    except Exception as e:
        print("Some other error: ", e)
    finally:
        # Если всё ещё открыто, можно закрыть
        if not websocket.client_state.name == "DISCONNECTED":
            await websocket.close()
@app.websocket("/igus")
async def igus_ws(websocket: WebSocket):
    """При запросе ws://host:port/color — коннектимся к ws://localhost:9998 и проксируем."""
    await websocket.accept()
    try:
        async with websockets.connect("ws://localhost:8020") as igus_ws:
            print("Connected to igus on 8020")  # <-- добавить
            await asyncio.gather(
                forward_messages_fastapi_to_websockets(websocket, igus_ws),
                forward_messages_websockets_to_fastapi(igus_ws, websocket)
            )
    except WebSocketDisconnect:
        # клиент (браузер) закрыл вкладку
        pass
    except Exception as e:
        print("Some other error: ", e)
    finally:
        # Если всё ещё открыто, можно закрыть
        if not websocket.client_state.name == "DISCONNECTED":
            await websocket.close()
# -------------------------------------------------------------
@app.get("/api/symovo_car/data")
def get_system_data():
    """
    Возвращает текущее состояние экземпляра symovo_car (AGV).
    """
    # last_update_time -- это datetime или None, преобразуем к строке
    last_update_str = str(symovo_car.last_update_time) if symovo_car.last_update_time else None

    # Формируем словарь с данными
    data = {
        "online": symovo_car.online,
        "last_update_time": last_update_str,
        "id": symovo_car.id,
        "name": symovo_car.name,
        "pose": {
            "x": symovo_car.pose_x,
            "y": symovo_car.pose_y,
            "theta": symovo_car.pose_theta,
            "map_id": symovo_car.pose_map_id
        },
        "velocity": {
            "x": symovo_car.velocity_x,
            "y": symovo_car.velocity_y,
            "theta": symovo_car.velocity_theta
        },
        "state": symovo_car.state,
        "battery_level": symovo_car.battery_level,
        "state_flags": symovo_car.state_flags,
        "robot_ip": symovo_car.robot_ip,
        "replication_port": symovo_car.replication_port,
        "api_port": symovo_car.api_port,
        "iot_port": symovo_car.iot_port,
        "last_seen": symovo_car.last_seen,
        "enabled": symovo_car.enabled,
        "last_update": symovo_car.last_update,
        "attributes": symovo_car.attributes,
        "planned_path_edges": symovo_car.planned_path_edges
    }
    return data

@app.get("/api/symovo_car/jobs")
def get_symovo_car_data():
    """
    Возвращает текущее состояние экземпляра symovo_car (AGV).
    """
    # Формируем словарь с данными
    data = symovo_car.get_jobs()
    return data

@app.get("/api/symovo_car/new_job")
def get_symovo_car_data(name: str = Query(...)):
    """
    Запускает работу go_to_position(...) по имени задания.
    """
    result = symovo_car.go_to_position(name,True,True)
    return {"status": "ok", "message": f"Going to position {name}", "result": result}

@app.get("/api/igus/data")
def get_igus_data():
    """
    Возвращает текущее состояние экземпляра igus_motor.
    """
    # last_update_time -- это datetime или None, преобразуем к строке
    last_update_str = str(igus_motor.last_update_time) if igus_motor.last_update_time else None

    # Формируем словарь с данными
    data = {
        "active": igus_motor.active,
        "ready": igus_motor.ready,
        "connected": igus_motor.connected,
        "last_update_str": last_update_str,
        "error": igus_motor.error,
        "homing": igus_motor.homing
        
    }
    return data

@app.get("/api/igus/command_operator")
def get_igus_data(
        command: str,
        position: int,
        velocity: int,
        acceleration: int,
        wait: bool = True
    ):
    data = {
        "command": command,
        "position": position,
        "velocity": velocity,
        "acceleration": acceleration,
        "wait": wait,
    }
    try:
        if "command" not in data:
            raise HTTPException(status_code=400, detail="No 'command' in JSON")
        
        return igus_lib.command_operator(data)
    
    except Exception as e:
        script_status = script_statuses[4]
        raise HTTPException(status_code=500, detail=f"Internal error: {e}")


@app.get("/api/xarm/data")
def get_xarm_data():
    """
    Возвращает текущее состояние экземпляра igus_motor.
    """
    data= {}
    data["command"] = "get_data"
    data["depth"] = 0
    result = xarm_command_operator(data)
    return result['result']

@app.get("/api/logs")
def get_logs(limit: int = None, level: str = None, type: str = None):
    """
    Получение логов сервера с возможностью фильтрации.
    
    Параметры:
    - limit: Ограничение количества возвращаемых записей
    - level: Фильтр по уровню логирования (debug, info, warning, error, critical)
    - type: Фильтр по типу вывода (stdout, stderr)
    """
    logs = server_logger.get_log_history(limit)
    
    # Применяем фильтры
    if level:
        logs = [log for log in logs if log.get('level') == level]
    if type:
        logs = [log for log in logs if log.get('type') == type]
        
    return JSONResponse(content={
        "status": "success",
        "count": len(logs),
        "logs": logs
    })

# ------------------- trajectory-------------------
@app.get("/api/trajectory")
def get_trajectory():
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT data FROM trajectory WHERE id = 1")
        row = c.fetchone()
        conn.close()
        if row:
            return json.loads(row[0])
        else:
            raise HTTPException(status_code=404, detail="Trajectory configuration not found.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/trajectory", status_code=201)
def save_trajectory(config: dict):
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        config_json = json.dumps(config, ensure_ascii=False)
        c.execute("UPDATE trajectory SET data = ? WHERE id = 1", (config_json,))
        if c.rowcount == 0:
            c.execute("INSERT INTO trajectory (id, data) VALUES (1, ?)", (config_json,))
        conn.commit()
        conn.close()
        return {"status": "ok", "message": "Trajectory configuration saved."}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))