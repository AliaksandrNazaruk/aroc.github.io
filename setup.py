from setuptools import setup
from glob import glob
import os

package_name = 'ros2_bridge'

setup(
    name=package_name,
    version='0.0.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'srv'), glob('srv/*.srv')),
    ],
    install_requires=['setuptools', 'rclpy', 'requests'],
    zip_safe=True,
    maintainer='maintainer',
    maintainer_email='maintainer@example.com',
    description='ROS2 bridge for Robot Control Server API',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'api_bridge = ros2_bridge.bridge:main',
        ],
    },
)
