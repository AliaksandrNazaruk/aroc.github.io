
import serial
import serial.tools.list_ports
import time
import threading

# Global lock for synchronizing access to the serial port
serial_lock = threading.Lock()

# Connection parameters
BAUDRATE = 9600
RECONNECT_DELAY = 1  # Delay before retrying connection (seconds)

def get_device_port(name):
    """
    Get serial port for a device by name.
    Returns the port or None if the device is not found.
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
    Initialize the serial port. Closes old connection if it exists and
    retries on failure.
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
    """Close the current serial connection."""
    try:
        if ser and ser.is_open:
            ser.close()
    except Exception as e:
        return


def send_command(command):
    """
    Send a command to Arduino over the serial port.
    Opens and closes the port every time a command is sent.
    """
    serial_conn = initialize_arduino()
    if not serial_conn or not serial_conn.is_open:
        return {"status": "error", "message": "Failed to open serial port."}
    try:
        with serial_lock:
            serial_conn.write(f"{command}\n".encode())
            time.sleep(0.25)  # Give Arduino time to process
            response = serial_conn.readline().decode().strip()
            return {"status": "success", "response": response}
    except serial.SerialException as e:
        return {"status": "error", "message": str(e)}
    finally:
        close_serial(serial_conn)
