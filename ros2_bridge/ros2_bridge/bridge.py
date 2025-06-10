import json
import requests

import rclpy
from rclpy.node import Node

from ros2_bridge.srv import CallAPI


class ApiBridge(Node):
    """ROS2 node bridging HTTP API calls."""

    def __init__(self):
        super().__init__('api_bridge')
        self.declare_parameter('base_url', 'http://localhost:8000')
        self.srv = self.create_service(CallAPI, 'call_api', self.handle_call_api)

    def handle_call_api(self, request, response):
        base_url = self.get_parameter('base_url').get_parameter_value().string_value
        url = base_url.rstrip('/') + request.endpoint
        data = None
        if request.json:
            try:
                data = json.loads(request.json)
            except json.JSONDecodeError as e:
                response.response = ''
                response.success = False
                response.error = f'Invalid JSON: {e}'
                return response
        try:
            r = requests.request(request.method.upper(), url, json=data)
            r.raise_for_status()
            response.response = r.text
            response.success = True
            response.error = ''
        except requests.RequestException as e:
            response.response = ''
            response.success = False
            response.error = str(e)
        return response


def main(args=None):
    rclpy.init(args=args)
    node = ApiBridge()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
