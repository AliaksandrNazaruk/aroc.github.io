# camera.py
import cv2
import numpy as np
import pyrealsense2 as rs
import logging

from core.robot_params import camera_width, camera_height, camera_fps

logger = logging.getLogger("camera")
# 141722072135
# 048522073892
def init_realsense(serial_number="141722072135", width=camera_width, height=camera_height, fps_color=camera_fps, fps_depth=camera_fps):
    pipeline = rs.pipeline(rs.context())
    config = rs.config()
    config.enable_device(serial_number)
    config.enable_stream(rs.stream.depth, width, height, rs.format.z16, fps_depth)
    config.enable_stream(rs.stream.color, width, height, rs.format.bgr8, fps_color)
    pipeline.start(config)
    device = pipeline.get_active_profile().get_device()
    advanced_mode = rs.rs400_advanced_mode(device)
    if not advanced_mode.is_enabled():
        advanced_mode.toggle_advanced_mode(True)
    logger.info("Камера RealSense инициализирована.")
    return pipeline

def process_depth_frame_with_data(depth_frame):
    try:
        depth_data = np.asanyarray(depth_frame.get_data())
        depth_data = cv2.rotate(depth_data, cv2.ROTATE_180)
        # Переводим данные из миллиметров в сантиметры
        depth_cm = depth_data.astype(np.float32) / 10.0
        h, w = depth_cm.shape
        centerX = w // 2
        centerY = h // 2
        center_depth = depth_cm[centerY, centerX]
        focalLength = 380.4253845214844
        camera_offset = 10.6
        effective_center = center_depth - camera_offset
        if effective_center <= 0:
            effective_center = 1.0
        pixelsPerCm = focalLength / effective_center
        halfSideX = int(1.5 * pixelsPerCm)
        halfSideY = int(1.5 * pixelsPerCm)
        pts = {
            "center": (centerX, centerY),
            "A": (max(0, centerX - halfSideX), max(0, centerY - halfSideY)),
            "B": (min(w-1, centerX + halfSideX), max(0, centerY - halfSideY)),
            "C": (max(0, centerX - halfSideX), min(h-1, centerY + halfSideY)),
            "D": (min(w-1, centerX + halfSideX), min(h-1, centerY + halfSideY))
        }
        depth_info = {}
        for key, (x, y) in pts.items():
            depth_info[key] = {
                "depth": float(depth_cm[y, x] - camera_offset),
                "coords": {"x": x, "y": y}
            }
        # Нормализация для визуализации
        depth_normalized = cv2.normalize(depth_data, None, 0, 255, cv2.NORM_MINMAX)
        depth_normalized = depth_normalized.astype(np.uint8)
        depth_color = cv2.applyColorMap(depth_normalized, cv2.COLORMAP_JET)
        return depth_color, depth_info
    except Exception as e:
        logger.error(f"Ошибка в process_depth_frame_with_data: {e}")
        return None, {}
