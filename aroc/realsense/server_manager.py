import asyncio
import sys
import signal
import logging
import os

logger = logging.getLogger("manager")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")

# Команда для запуска серверного процесса.
# Используем sys.executable, чтобы запускать с тем же интерпретатором,
# и формируем путь к файлу server.py (он должен находиться в той же директории).
SERVER_PATH = os.path.join(os.path.dirname(__file__), "server.py")
SERVER_CMD = [sys.executable, SERVER_PATH]

RESTART_DELAY = 5  # задержка перед перезапуском (в секундах)

async def run_server():
    """
    Запускает серверный процесс как подпроцесс, выводит его stdout и stderr.
    Если процесс завершается, возвращает его код.
    """
    logger.info("Запуск серверного процесса...")
    proc = await asyncio.create_subprocess_exec(
        *SERVER_CMD,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    # Задачи для чтения stdout и stderr
    stdout_task = asyncio.create_task(read_stream(proc.stdout, "STDOUT"))
    stderr_task = asyncio.create_task(read_stream(proc.stderr, "STDERR"))
    try:
        returncode = await proc.wait()
        logger.error(f"Сервер завершился с кодом {returncode}")
    except Exception as e:
        logger.error(f"Ошибка серверного процесса: {e}")
        returncode = -1
    finally:
        stdout_task.cancel()
        stderr_task.cancel()
    return returncode

async def read_stream(stream, label):
    """
    Читает и логирует строки из потока (stdout или stderr) серверного процесса.
    """
    while True:
        line = await stream.readline()
        if not line:
            break
        logger.info(f"{label}: {line.decode().rstrip()}")

async def run_manager():
    """
    Запускает серверный процесс в цикле. Если сервер завершился,
    ждёт RESTART_DELAY секунд и запускает его снова.
    """
    while True:
        code = await run_server()
        logger.info(f"Перезапуск сервера через {RESTART_DELAY} секунд...")
        await asyncio.sleep(RESTART_DELAY)

def shutdown():
    logger.info("Остановка менеджера...")
    for task in asyncio.all_tasks():
        task.cancel()

if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    # Добавляем обработчики сигналов для корректного завершения
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, shutdown)
    try:
        loop.run_until_complete(run_manager())
    except asyncio.CancelledError:
        logger.info("Менеджер остановлен.")
    finally:
        loop.close()
