import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import AnyLaunchDescriptionSource
from launch_ros.actions import Node


def generate_launch_description():
    # Foxglove Bridge 런치파일 경로 설정
    foxglove_bridge_pkg = get_package_share_directory('foxglove_bridge')
    foxglove_bridge_launch = IncludeLaunchDescription(
        AnyLaunchDescriptionSource(
            os.path.join(foxglove_bridge_pkg, 'launch', 'foxglove_bridge_launch.xml')
        )
    )
    

    return LaunchDescription([
        # Foxglove Bridge 실행
        foxglove_bridge_launch,
        

        # 중앙 TG30 정렬 (laser_frame)
        Node(
            package='tf2_ros',
            executable='static_transform_publisher',
            name='static_tf_pub_center',
            arguments=['0', '0', '0', '0', '0', '0', 'base_link', 'laser_frame']
        ),
        

        # 오른쪽 GS2 정렬 (laser_right_frame)
        Node(
            package='tf2_ros',
            executable='static_transform_publisher',
            name='static_tf_pub_right',
            arguments=['0', '0', '0', '0', '0', '0', 'base_link', 'laser_right_frame']
        ),
        

        # 왼쪽 GS2 정렬 (laser_left_frame)
        Node(
            package='tf2_ros',
            executable='static_transform_publisher',
            name='static_tf_pub_left',
            arguments=['0', '0', '0', '0', '0', '0', 'base_link', 'laser_left_frame']
        ),
    ])