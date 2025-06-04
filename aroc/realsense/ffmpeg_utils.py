import asyncio
import logging

logger = logging.getLogger("ffmpeg_utils")

async def start_ffmpeg(width=640, height=480, fps=15):
    cmd = [
        'ffmpeg',
        '-f', 'rawvideo',
        '-pixel_format', 'bgr24',
        '-video_size', f'{width}x{height}',
        '-framerate', str(fps),
        '-i', '-',  # вход из stdin
        '-vf', 'format=yuv420p',
        '-c:v', 'libx264',
        '-preset', 'ultrafast',
        '-tune', 'zerolatency',
        '-g', str(fps),
        '-x264opts', f'keyint={fps}:scenecut=0:repeat-headers=1',
        '-f', 'h264',
        '-'  # вывод в stdout
    ]
    logger.info("Запуск ffmpeg для цветного потока: " + " ".join(cmd))
    proc = await asyncio.create_subprocess_exec(*cmd,
                                                 stdin=asyncio.subprocess.PIPE,
                                                 stdout=asyncio.subprocess.PIPE,
                                                 stderr=asyncio.subprocess.PIPE)
    return proc

async def start_depth_ffmpeg(width=640, height=480, fps=15):
    cmd = [
        'ffmpeg',
        '-f', 'rawvideo',
        '-pixel_format', 'bgr24',
        '-video_size', f'{width}x{height}',
        '-framerate', str(fps),
        '-i', '-',  # вход из stdin
        '-vf', 'format=yuv420p',
        '-c:v', 'libx264',
        '-preset', 'ultrafast',
        '-tune', 'zerolatency',
        '-g', str(fps),
        '-x264opts', f'keyint={fps}:scenecut=0:repeat-headers=1',
        '-f', 'h264',
        '-'  # вывод в stdout
    ]
    logger.info("Запуск ffmpeg для глубинного потока: " + " ".join(cmd))
    proc = await asyncio.create_subprocess_exec(*cmd,
                                                 stdin=asyncio.subprocess.PIPE,
                                                 stdout=asyncio.subprocess.PIPE,
                                                 stderr=asyncio.subprocess.PIPE)
    return proc
