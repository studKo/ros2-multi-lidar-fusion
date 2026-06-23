from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    # --- [1] Static TF Publisher (왼쪽 센서 3개 좌표) ---
    
    # 1. 왼쪽 TG30 (Z: 0.11, Yaw: 1.5708)
    tf_left_tg30 = Node(
        package='tf2_ros', 
        executable='static_transform_publisher', 
        name='tf_left_tg30',
        arguments=['0.05', '0.265', '0.11', '1.5708', '0', '0', 'base_link', 'left_lidar_TG30']
    )

    # 2. 왼쪽 GS2 전방 (Z: 0.07, Yaw: 1.5708)
    tf_left_gs2_front = Node(
        package='tf2_ros', 
        executable='static_transform_publisher', 
        name='tf_left_gs2_front',
        arguments=['0.47', '0.3', '0.07', '1.5708', '0', '0', 'base_link', 'left_gs2_lidar_front']
    )

    # 3. 왼쪽 GS2 후방 (Z: 0.07, Yaw: 1.5708)
    tf_left_gs2_rear = Node(
        package='tf2_ros', 
        executable='static_transform_publisher', 
        name='tf_left_gs2_rear',
        arguments=['-0.47', '0.3', '0.07', '1.5708', '0', '0', 'base_link', 'left_gs2_lidar_rear']
    )

    # --- [2] 드라이버 노드 실행 ---
    return LaunchDescription([
        # 왼쪽 TG30 드라이버
        # 오른쪽 TG30 드라이버
        # 왼쪽 TG30 드라이버
        Node(
            package='lidar_control', 
            executable='tg30_bypasser', 
            name='tg30_bypasser_left',
            parameters=[{
                'serial_port': '/dev/serial/by-path/platform-xhci-hcd.0-usb-0:2:1.0-port0',
                'frame_id': 'left_lidar_TG30'
            }],
            remappings=[
                ('/scan', '/lidar_left_tg30/scan')
            ]
        ),
        tf_left_tg30,

        # 왼쪽 GS2 전방 드라이버
        Node(
            package='lidar_control', 
            namespace='lidar_left_front', 
            executable='gs2_bypasser', 
            name='bypasser_left_front',
            parameters=[{
                'serial_port': '/dev/serial/by-path/platform-xhci-hcd.1-usb-0:1:1.0-port0',
                'scan_topic': 'scan', 
                'frame_id': 'left_gs2_lidar_front'
            }]
        ),
        tf_left_gs2_front,

        # 왼쪽 GS2 후방 드라이버
        Node(
            package='lidar_control', 
            namespace='lidar_left_rear', 
            executable='gs2_bypasser', 
            name='bypasser_left_rear',
            parameters=[{
                'serial_port': '/dev/serial/by-path/platform-xhci-hcd.0-usb-0:1:1.0-port0',
                'scan_topic': 'scan', 
                'frame_id': 'left_gs2_lidar_rear'
            }]
        ),
        tf_left_gs2_rear,
    ])