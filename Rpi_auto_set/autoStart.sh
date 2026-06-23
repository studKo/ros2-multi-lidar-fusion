#!/bin/bash
# 환경 변수 로드 (절대 경로 사용 필수!)
source /opt/ros/jazzy/setup.bash
source /home/rpileft/project/install/setup.bash

# 통신 설정
export ROS_AUTOMATIC_DISCOVERY_RANGE=SUBNET
export ROS_DOMAIN_ID=0

# 1. 런치 파일 백그라운드 실행
ros2 launch lidar_control lidars_launch.py &
LIDAR_PID=$!

# 2. 라이다 부팅 대기
sleep 10

# 3. 모터 회전 시작 명령어('s') 전송
ros2 topic pub --once /total_lidar_cmd std_msgs/msg/String "{data: 's'}"

# 4. 프로세스 유지
wait $LIDAR_PID