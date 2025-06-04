
import serial
import serial.tools.list_ports
import time
import threading

# Глобальная блокировка для синхронизации работы с последовательным портом
serial_lock = threading.Lock()

# Параметры подключения
BAUDRATE = 9600
RECONNECT_DELAY = 1  # Задержка перед повторной попыткой подключения (в секундах)

def get_device_port(name):
    """
    Получение последовательного порта для устройства по имени.
    Возвращает порт или None, если устройство не найдено.
    """
    try:
        ports = serial.tools.list_ports.comports()
        vid = None
        pid = None
        if name == 'arduino':
            pid = 32823
            vid = 9025
            for port in ports:
                if port.vid == vid and port.pid == pid:
                    return port
    except Exception as e:
        return None
    return None

def initialize_arduino():
    """
    Инициализация последовательного порта. Закрывает старое соединение, если оно существует.
    Повторные попытки соединения при неудаче.
    """
    try:
        port = get_device_port('arduino')
        if port is not None:
            ser = serial.Serial(port.device, BAUDRATE, timeout=1)
            if ser.is_open:
                return ser
    except serial.SerialException as e:
        return None
    return None


def close_serial(ser):
    """
    Закрытие текущего соединения с последовательным портом.
    """
    try:
        if ser and ser.is_open:
            ser.close()
    except Exception as e:
        return


def send_command(command):
    """
    Отправляет команду на Arduino через последовательный порт.
    Открывает и закрывает порт каждый раз при отправке команды.
    """
    serial_conn = initialize_arduino()
    if not serial_conn or not serial_conn.is_open:
        return {"status": "error", "message": "Failed to open serial port."}
    try:
        with serial_lock:
            serial_conn.write(f"{command}\n".encode())
            time.sleep(0.25)  # Даем Arduino время обработать
            response = serial_conn.readline().decode().strip()
            return {"status": "success", "response": response}
    except serial.SerialException as e:
        return {"status": "error", "message": str(e)}
    finally:
        close_serial(serial_conn)
