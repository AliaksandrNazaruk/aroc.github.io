import pyrealsense2 as rs
import numpy as np
import base64
import cv2

pipeline_started = False  

def start(SERIAL_NUMBER,color=True,depth=True):
    global pipeline_started
    print("Инициализация камеры...")
    pipeline_started = False  # Флаг успешного запуска pipeline
    pipeline = rs.pipeline(rs.context())
    config = rs.config()
    config.enable_device(SERIAL_NUMBER) 
    if depth:
        config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)
    if color:
        config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 15)
    pipeline.start(config)
    device = pipeline.get_active_profile().get_device()
    advanced_mode = rs.rs400_advanced_mode(device)
    if not advanced_mode.is_enabled():
        advanced_mode.toggle_advanced_mode(True)
    pipeline_started = True
    return pipeline

async def depth_base64(pipeline):
    frames = pipeline.wait_for_frames()
    depth_frame = frames.get_depth_frame()
    depth_image_filled = np.asanyarray(depth_frame.get_data())
    depth_image_filled = cv2.rotate(depth_image_filled, cv2.ROTATE_180)
    mask = (depth_image_filled == 0).astype(np.uint8)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (10, 10))
    dilated_mask = cv2.dilate(mask, kernel, iterations=1)
    depth_image_filled = cv2.inpaint(depth_image_filled, dilated_mask, inpaintRadius=1, flags=cv2.INPAINT_TELEA)
    average_depth_bytes = depth_image_filled.tobytes()
    average_depth_base64 = base64.b64encode(average_depth_bytes).decode('utf-8')
    return average_depth_base64

async def color_base64(pipeline):
    frames = pipeline.wait_for_frames()
    color_frame = frames.get_color_frame()
    color_data = np.asanyarray(color_frame.get_data())
    color_data = cv2.rotate(color_data, cv2.ROTATE_180)
    _, buffer = cv2.imencode('.jpg', color_data)
    image_base64 = base64.b64encode(buffer).decode('utf-8')
    return image_base64
