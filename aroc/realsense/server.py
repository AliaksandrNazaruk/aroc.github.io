import asyncio
import signal
import sys
import logging
import websockets
import json
import cv2
import numpy as np

from core.connection_config import (
    realsense_color_host,
    realsense_color_port,
    realsense_depth_host,
    realsense_depth_port,
)
from core.robot_params import camera_fps

from camera import init_realsense, process_depth_frame_with_data
from ffmpeg_utils import start_ffmpeg, start_depth_ffmpeg
from connection_manager import ConnectionManager

logger = logging.getLogger("server")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")

# Глобальные менеджеры подключений для разных потоков
color_manager = ConnectionManager("color")
depth_manager = ConnectionManager("depth")

async def color_handler(websocket, path):
    await color_manager.register(websocket)
    try:
        async for _ in websocket:
            pass  # Если необходимо обрабатывать входящие сообщения
    except Exception as e:
        logger.error(f"Ошибка у клиента color: {e}")
    finally:
        await color_manager.unregister(websocket)

async def depth_handler(websocket, path):
    await depth_manager.register(websocket)
    try:
        async for _ in websocket:
            pass
    except Exception as e:
        logger.error(f"Ошибка у клиента depth: {e}")
    finally:
        await depth_manager.unregister(websocket)

async def capture_frames_task(pipeline, color_ffmpeg, fps=camera_fps):
    frame_interval = 1.0 / fps
    loop = asyncio.get_event_loop()
    while True:
        try:
            frames = await loop.run_in_executor(None, pipeline.wait_for_frames)
            
            # Цветной кадр
            color_frame = frames.get_color_frame()
            if color_frame:
                color_data = np.asanyarray(color_frame.get_data())
                color_data = cv2.rotate(color_data, cv2.ROTATE_180)
                try:
                    color_ffmpeg.stdin.write(color_data.tobytes())
                    try:
                        await asyncio.wait_for(color_ffmpeg.stdin.drain(), timeout=1.0)
                    except asyncio.TimeoutError:
                        logger.error("Timeout при ожидании drain() у ffmpeg.stdin для color потока")
                        sys.exit(1)
                        
                except (BrokenPipeError, ConnectionResetError) as e:
                    logger.error("Ошибка записи в ffmpeg для color потока: " + str(e))
                    sys.exit(1)

        except Exception as e:
            logger.error(f"Ошибка в capture_frames_task: {e}")
        await asyncio.sleep(frame_interval)

async def broadcast_stream_task(ffmpeg_proc, manager, stream_type, read_chunk_size=4096):
    while True:
        try:
            chunk = await ffmpeg_proc.stdout.read(read_chunk_size)
            if not chunk:
                if ffmpeg_proc.returncode is not None:
                    logger.error(f"Процесс FFmpeg для {stream_type} потока завершился.")
                    break
                await asyncio.sleep(0.01)
                continue
            await manager.broadcast(chunk)
        except Exception as e:
            logger.error(f"Ошибка при рассылке {stream_type} потока: {e}")
            await asyncio.sleep(0.01)

async def broadcast_depth_info_task(depth_info_queue):
    while True:
        try:
            depth_info = await depth_info_queue.get()
            await depth_manager.broadcast(depth_info)
        except Exception as e:
            logger.error("Ошибка рассылки данных глубины: " + str(e))
        await asyncio.sleep(0.001)

async def main():
    logger.info("Запуск main()")
    try:
        pipeline = init_realsense()
    except Exception as e:
        logger.error(f"Ошибка инициализации камеры: {e}")
        return

    depth_info_queue = asyncio.Queue(maxsize=1)

    try:
        # Запуск ffmpeg-процессов через asyncio
        color_ffmpeg = await start_ffmpeg()
        # depth_ffmpeg = await start_depth_ffmpeg()
    except Exception as e:
        logger.error(f"Ошибка запуска ffmpeg-процессов: {e}")
        return

    try:
        # Запуск WebSocket серверов
        color_server = await websockets.serve(
            color_handler,
            realsense_color_host,
            realsense_color_port,
            ping_interval=5,
            ping_timeout=5,
        )
        # depth_server = await websockets.serve(depth_handler, realsense_depth_host, realsense_depth_port, ping_interval=5, ping_timeout=5)
    except Exception as e:
        logger.error(f"Ошибка запуска WebSocket серверов: {e}")
        return

    logger.info("Инициализация завершена, сервер работает.")

    # Создаём фоновые задачи
    asyncio.create_task(capture_frames_task(pipeline, color_ffmpeg))
    asyncio.create_task(broadcast_stream_task(color_ffmpeg, color_manager, "color"))
    # asyncio.create_task(broadcast_stream_task(depth_ffmpeg, depth_manager, "depth"))
    # asyncio.create_task(broadcast_depth_info_task(depth_info_queue))

    logger.info("Задачи запущены, ожидаем бесконечно")
    # Ждём бесконечно
    stop_event = asyncio.Event()
    await stop_event.wait()
    logger.info("Stop event наступил, выходим из main()")



def shutdown(sig, loop):
    logger.info(f"Получен сигнал завершения {sig.name}. Отмена всех задач...")
    for task in asyncio.all_tasks(loop):
        task.cancel()
    loop.stop()

if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    for s in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(s, lambda s=s: shutdown(s, loop))
    try:
        loop.run_until_complete(main())
    except asyncio.CancelledError:
        logger.info("Все задачи отменены, сервер завершается.")
    finally:
        loop.close()
        sys.exit(0)
