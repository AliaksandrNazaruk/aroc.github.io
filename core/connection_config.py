# Connection parameters for robot components and services

# Robot hardware IP addresses
xarm_manipulator_ip = "127.0.0.1"
symovo_car_ip = "192.168.1.100"
web_server_ip = "127.0.0.1"
igus_motor_ip = "127.0.0.1"

# Misc numbers
symovo_car_number = 15

# Ports and hosts
igus_motor_port = 512
igus_ws_host = "0.0.0.0"
igus_ws_port = 8020

web_server_host = "0.0.0.0"
web_server_port = 8000

realsense_color_host = "0.0.0.0"
realsense_color_port = 9998
realsense_depth_host = "0.0.0.0"
realsense_depth_port = 9999
realsense_depth_query_port = 10000

# External WebSocket URLs
camera_depth_ws_url = "ws://192.168.1.55:9999"
camera_depth_query_ws_url = "ws://192.168.1.55:10000"
camera_color_ws_url = "ws://192.168.1.55:9998"
camera2_ws_url = "ws://localhost:9998"
igus_ws_url = "ws://localhost:8020"
