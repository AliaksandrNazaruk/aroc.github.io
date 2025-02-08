import asyncio
import websockets
import time
import logging
import psutil
from websocket_lib import is_port_in_use, kill_process_using_port, handle_client, send_data_to_clients
from realsense_lib import start, color_base64, depth_base64

# Серверные переменные
SERVER_PORT = 9999
RETRY_DELAY = 5  # Задержка между попытками подключиться к камере
SERIAL_NUMBER = "048522073892"

# Логирование ошибок
logging.basicConfig(filename="server_logs.log", level=logging.INFO, format='%(asctime)s - %(message)s')

# Функция для отправки уведомлений о критичных ошибках
def send_alert(message):
    # Здесь можно интегрировать реальную систему уведомлений (email, SMS, etc.)
    logging.critical(f"ALERT: {message}")
    print(f"ALERT: {message}")

# Функция для запуска камеры с повторными попытками
def start_camera_with_retries():
    while True:
        try:
            print("Инициализация камеры...")
            pipeline = start(SERIAL_NUMBER)
            print("RealSense камера успешно запущена")
            return pipeline
        except RuntimeError as e:
            if "No device connected" in str(e):
                print(f"Ошибка: камера не подключена. Ожидаем {RETRY_DELAY} секунд...")
                send_alert(f"Ошибка: камера не подключена.")
            else:
                print(f"Ошибка при инициализации камеры: {e}")
                send_alert(f"Ошибка при инициализации камеры: {e}")
            
            # Ждем перед повторной попыткой
            time.sleep(RETRY_DELAY)

# Функция для отправки изображений клиентам
async def send_images_to_clients(pipeline):
    try:
        while True:
            # Получаем изображение и передаем клиентам
            depth_image_base64 = await depth_base64(pipeline)
            color_base64_ = await color_base64(pipeline)
            await send_data_to_clients(depth_image_base64)
            await send_data_to_clients(color_base64_)
            await asyncio.sleep(0.1)  # Пауза между отправками
    except Exception as e:
        logging.error(f"Ошибка в отправке изображений: {e}")
        await asyncio.sleep(1)  # Повторная попытка через 1 секунду

# Функция для проверки системных ресурсов
def check_system_resources():
    cpu_usage = psutil.cpu_percent()
    memory_usage = psutil.virtual_memory().percent

    if cpu_usage > 80:
        send_alert(f"Высокая загрузка процессора: {cpu_usage}%")
    if memory_usage > 80:
        send_alert(f"Высокое использование памяти: {memory_usage}%")

# Функция для запуска WebSocket сервера
async def start_server():
    if is_port_in_use(SERVER_PORT):
        logging.warning(f"Порт {SERVER_PORT} уже используется. Попробуем завершить процесс.")
        if kill_process_using_port(SERVER_PORT):
            logging.info(f"Процесс на порту {SERVER_PORT} завершен. Попробуем запустить сервер снова.")
        else:
            send_alert(f"Не удалось завершить процесс на порту {SERVER_PORT}. Завершаем выполнение.")
            return
    
    pipeline = start_camera_with_retries()  # Бесконечная попытка подключения к камере
    if pipeline is None:
        send_alert("Не удалось запустить камеру RealSense. Завершаем выполнение.")
        return

    try:
        server = await websockets.serve(handle_client, "0.0.0.0", SERVER_PORT)
        logging.info(f"WebSocket сервер запущен на ws://0.0.0.0:{SERVER_PORT}")
        await send_images_to_clients(pipeline)
        await server.wait_closed()

    except Exception as e:
        logging.error(f"Ошибка при запуске WebSocket сервера: {e}")
        send_alert(f"Ошибка при запуске WebSocket сервера: {e}")
        await restart_server()

# Функция для перезапуска сервера
async def restart_server():
    logging.info("Перезапуск сервера...")
    await asyncio.sleep(2)  # Задержка перед перезапуском
    await main()  # Рекурсивный вызов для перезапуска

# Основная асинхронная функция
async def main():
    # Проверка системных ресурсов перед запуском
    check_system_resources()
    
    await start_server()

# Запуск сервера
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        logging.critical(f"Критическая ошибка в основном потоке: {e}")
        send_alert(f"Критическая ошибка в основном потоке: {e}")
        # Попытка перезапуска при критической ошибке
        time.sleep(5)
        asyncio.run(main())
