# tasks.py
import asyncio
import cv2
import json
import logging
import numpy as np
from camera import process_depth_frame_with_data

logger = logging.getLogger("tasks")
# Импортируем множества клиентов из обработчиков (или можно импортировать их в main)
from websocket_handlers import connected_color_clients, connected_depth_clients

async def capture_frames_task(pipeline, ffmpeg_proc, depth_ffmpeg_proc, depth_info_queue):
    from core.robot_params import camera_fps
    fps = camera_fps
    frame_interval = 1.0 / fps
    while True:
        try:
            frames = pipeline.wait_for_frames()
            # Цветной поток
            color_frame = frames.get_color_frame()
            if color_frame:
                color_data = np.asanyarray(color_frame.get_data())
                color_data = cv2.rotate(color_data, cv2.ROTATE_180)
                try:
                    ffmpeg_proc.stdin.write(color_data.tobytes())
                except BrokenPipeError:
                    logger.error("BrokenPipeError при записи в ffmpeg для цветного потока.")
            
            # Глубинный поток
            depth_frame = frames.get_depth_frame()
            if depth_frame:
                depth_color, depth_values = process_depth_frame_with_data(depth_frame)
                if depth_color is not None:
                    try:
                        depth_ffmpeg_proc.stdin.write(depth_color.tobytes())
                    except BrokenPipeError:
                        logger.error("BrokenPipeError при записи в ffmpeg для глубинного потока.")
                    if depth_info_queue.empty():
                        depth_info_queue.put_nowait(json.dumps(depth_values))
        except Exception as e:
            logger.error(f"Ошибка в capture_frames_task: {e}")
        await asyncio.sleep(frame_interval)

async def broadcast_color_task(ffmpeg_proc):
    loop = asyncio.get_running_loop()
    chunk_count = 0
    def read_stdout(num_bytes=4096):
        if ffmpeg_proc.poll() is not None:
            return b''
        return ffmpeg_proc.stdout.read(num_bytes)
    
    while True:
        chunk = await loop.run_in_executor(None, read_stdout)
        if not chunk:
            await asyncio.sleep(0.01)
            if ffmpeg_proc.poll() is not None:
                logger.error("ffmpeg для цветного потока завершился.")
                err_data = ffmpeg_proc.stderr.read().decode('utf-8', errors='replace')
                logger.error("FFmpeg stderr: " + err_data)
                break
            continue
        chunk_count += 1
        if chunk_count % 100 == 0:
            logger.debug(f"[COLOR] Отправлено {chunk_count} блоков, клиентов: {len(connected_color_clients)}")
        stale_clients = []
        for ws in list(connected_color_clients):
            try:
                await ws.send(chunk)
            except Exception as e:
                logger.error(f"[COLOR] Ошибка отправки клиенту {ws.remote_address}: {e}")
                stale_clients.append(ws)
        for ws in stale_clients:
            connected_color_clients.remove(ws)

async def broadcast_depth_color_task(depth_ffmpeg_proc):
    loop = asyncio.get_running_loop()
    chunk_count = 0
    def read_stdout(num_bytes=4096):
        if depth_ffmpeg_proc.poll() is not None:
            return b''
        return depth_ffmpeg_proc.stdout.read(num_bytes)
    
    while True:
        chunk = await loop.run_in_executor(None, read_stdout)
        if not chunk:
            await asyncio.sleep(0.01)
            if depth_ffmpeg_proc.poll() is not None:
                logger.error("ffmpeg для глубинного потока завершился.")
                err_data = depth_ffmpeg_proc.stderr.read().decode('utf-8', errors='replace')
                logger.error("FFmpeg (depth) stderr: " + err_data)
                break
            continue
        chunk_count += 1
        if chunk_count % 100 == 0:
            logger.debug(f"[DEPTH] Отправлено {chunk_count} блоков, клиентов: {len(connected_depth_clients)}")
        stale_clients = []
        for ws in list(connected_depth_clients):
            try:
                await ws.send(chunk)
            except Exception as e:
                logger.error(f"[DEPTH] Ошибка отправки клиенту {ws.remote_address}: {e}")
                stale_clients.append(ws)
        for ws in stale_clients:
            connected_depth_clients.remove(ws)

async def broadcast_depth_info_task(depth_info_queue):
    while True:
        try:
            depth_info = await depth_info_queue.get()
            stale_clients = []
            for ws in list(connected_depth_clients):
                try:
                    await ws.send(depth_info)
                except Exception as e:
                    logger.error(f"[DEPTH] Ошибка отправки JSON клиенту {ws.remote_address}: {e}")
                    stale_clients.append(ws)
            for ws in stale_clients:
                connected_depth_clients.remove(ws)
        except Exception as e:
            logger.error(f"[DEPTH] Ошибка в broadcast_depth_info_task: {e}")
        await asyncio.sleep(0.001)
