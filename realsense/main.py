# main.py
import asyncio
import signal
import sys
import logging

import websockets

from core.connection_config import (
    realsense_color_host,
    realsense_color_port,
    realsense_depth_host,
    realsense_depth_port,
)
from core.robot_params import camera_fps

from camera import init_realsense
from ffmpeg_utils import start_ffmpeg, start_depth_ffmpeg
from websocket_handlers import handle_color_connection, handle_depth_connection
from tasks import capture_frames_task, broadcast_color_task, broadcast_depth_color_task, broadcast_depth_info_task

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("main")

async def main():
    pipeline = init_realsense()

    # Запуск WebSocket серверов
    color_server = await websockets.serve(
        handle_color_connection,
        realsense_color_host,
        realsense_color_port,
        ping_interval=5,
        ping_timeout=5,
        close_timeout=2,
    )
    depth_server = await websockets.serve(
        handle_depth_connection,
        realsense_depth_host,
        realsense_depth_port,
        ping_interval=5,
        ping_timeout=5,
        close_timeout=2,
    )
    logger.info(
        f"WebSocket серверы запущены: цветной (порт {realsense_color_port}), "
        f"глубинный (порт {realsense_depth_port})."
    )

    # Запуск ffmpeg-процессов
    ffmpeg_proc = start_ffmpeg()
    depth_ffmpeg_proc = start_depth_ffmpeg()
    logger.info("ffmpeg запущен для H.264 кодирования потоков.")

    # Очередь для JSON-информации о глубине
    depth_info_queue = asyncio.Queue(maxsize=1)

    # Создание задач
    capture_task = asyncio.create_task(capture_frames_task(pipeline, ffmpeg_proc, depth_ffmpeg_proc, depth_info_queue))
    broadcast_color = asyncio.create_task(broadcast_color_task(ffmpeg_proc))
    broadcast_depth_color = asyncio.create_task(broadcast_depth_color_task(depth_ffmpeg_proc))
    broadcast_depth_info = asyncio.create_task(broadcast_depth_info_task(depth_info_queue))

    tasks = [capture_task, broadcast_color, broadcast_depth_color, broadcast_depth_info]

    try:
        await asyncio.gather(*tasks)
    except asyncio.CancelledError:
        logger.info("Задачи были отменены.")

async def shutdown(server_tasks, tasks):
    logger.info("Начало завершения работы...")
    for server in server_tasks:
        server.close()
        await server.wait_closed()
    for task in tasks:
        task.cancel()
    await asyncio.gather(*tasks, return_exceptions=True)
    logger.info("Завершение работы завершено.")

if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    main_task = loop.create_task(main())

    def handle_shutdown():
        logger.info("Получен сигнал завершения, отменяем все задачи...")
        for task in asyncio.all_tasks(loop):
            task.cancel()

    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, handle_shutdown)

    try:
        loop.run_until_complete(main_task)
    except KeyboardInterrupt:
        logger.info("KeyboardInterrupt, завершаем работу.")
    finally:
        pending = asyncio.all_tasks(loop)
        loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
        loop.run_until_complete(loop.shutdown_asyncgens())
        loop.close()
        sys.exit(0)
