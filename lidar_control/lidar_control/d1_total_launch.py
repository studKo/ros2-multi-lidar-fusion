import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    # 1. 100번 라이다 드라이버
    d1_100_node = Node(
        package='seyond', 
        executable='seyond_node',
        name='seyond_d1_100',
        output='screen',
        parameters=[{
            'lidar_ip': '192.168.0.100',
            'port': 8010,
            'frame_id': 'd1_100_link' # 100번 전용 이름표
        }]
    )

    # 2. 101번 라이다 드라이버
    d1_101_node = Node(
        package='seyond', 
        executable='seyond_node',
        name='seyond_d1_101',
        output='screen',
        parameters=[{
            'lidar_ip': '192.168.0.101',
            'port': 8010,
            'frame_id': 'd1_101_link' # 101번 전용 이름표
        }]
    )

    # 참고: Foxglove Bridge와 TF는 만든었던
    # ~/cam_workspace/foxglove_launch.py 에서 한꺼번에 관리하므로 
    # 여기서는 드라이버만 실행합니다.

    return LaunchDescription([
        d1_100_node,
        d1_101_node
    ])