# ROS2 Multi-LiDAR Fusion and Visualization System

![ROS2](https://img.shields.io/badge/ROS2-Jazzy-22314E?logo=ros)
![Ubuntu](https://img.shields.io/badge/Ubuntu-24.04-E95420?logo=ubuntu)

## 1. 센서 드라이버 설치 및 초기 설정 (Sensor Driver Installation & Initial Setup)

### 1.1 Seyond Hummingbird D1 SDK 설치 및 네트워크 설정

Hummingbird D1 센서를 사용하기 위해서는 공식 SDK 설치 및 센서 IP 설정이 필요합니다.

#### 1) SDK 압축 해제

```bash
tar -xzvf inno-lidar-sdk-release-client-sdk-3.103.7-public.tgz
cd ~/SDK_file_path
```

#### 2) SDK 빌드

드라이버 폴더에서 빌드 스크립트를 실행합니다.

```bash
./build.sh
```

#### 3) 센서 네트워크 설정

기본 IP 주소를 프로젝트 네트워크 대역으로 변경합니다.

예시 (센서 IP를 `172.168.1.10`에서 `192.168.5.100`으로 변경):

```bash
cd apps/tools/lidar_util

./innovusion_lidar_util \
172.168.1.10 \
set_network \
192.168.5.100 \
255.255.255.0 \
192.168.5.1
```

---

### 1.2 YDLidar SDK 및 ROS2 Driver 설치

TG30 및 GS2 센서를 사용하기 위해서는 YDLidar SDK와 ROS2 드라이버 설치가 필요합니다.

#### 1) YDLidar SDK 설치

```bash
git clone [https://github.com/YDLIDAR/YDLidar-SDK.git](https://github.com/YDLIDAR/YDLidar-SDK.git)

cd YDLidar-SDK
mkdir build
cd build

cmake ..
make

sudo make install
```

#### 2) ROS2 Driver 설치

ROS2 워크스페이스의 `src` 폴더에서 드라이버를 다운로드합니다.

```bash
cd ~/ros2_ws/src

git clone [https://github.com/YDLIDAR/ydlidar_ros2_driver.git](https://github.com/YDLIDAR/ydlidar_ros2_driver.git)
```

빌드 후 환경을 적용합니다.

```bash
cd ~/ros2_ws

colcon build --packages-select ydlidar_ros2_driver

source install/setup.bash
```

#### 3) 장치 연결 확인

USB 장치가 정상적으로 인식되었는지 확인합니다.

```bash
ls /dev/ttyUSB*
```


```bash
ls /dev/ydlidar*
```

---

## 2. 프로젝트 개요 (Project Overview)

본 프로젝트는 다수의 이기종 라이다(LiDAR) 센서를 단일 Ubuntu 서버 환경에서 동시에 제어하고 데이터를 통합하여 수신 및 시각화하는 ROS2 패키지(`lidar_control`)입니다. 총 8개의 라이다 센서 데이터를 정적 TF(Static Transform)를 통해 단일 좌표계로 병합하고, Foxglove Studio를 활용해 실시간 3D 통합 시각화를 제공합니다.

### 지원 센서 목록 (총 8대)
* **Seyond Hummingbird D1** x 2대
* **YDLidar TG30** x 2대
* **YDLidar GS2** x 4대

---

## 3. 시스템 요구사항 (System Requirements)

* **OS**: Ubuntu 24.04 LTS
* **Middleware**: ROS2 Jazzy Jalisco
* **Visualization**: Foxglove Studio
* **Network**: 다중 이더넷 인터페이스를 위한 Netplan 구성

---

## 4. 하드웨어 및 네트워크 구성 (Hardware & Network Configuration)

각 센서 및 중간 컨트롤러(Raspberry Pi)의 고정 IP 설정 및 통신 방식은 다음과 같습니다. 원활한 통신을 위해 호스트 서버의 이더넷 인터페이스도 동일 대역으로 설정되어야 합니다.

| 장치명 (Device) | 수량 | 통신 방식 | IP 주소 (IP Address) | 역할 |
| :--- | :---: | :--- | :--- | :--- |
| **Hummingbird D1 (Left)** | 1 | Ethernet / UDP | `192.168.5.100` | 3D PointCloud 데이터 수집 |
| **Hummingbird D1 (Right)**| 1 | Ethernet / UDP | `192.168.5.101` | 3D PointCloud 데이터 수집 |
| **Raspberry Pi 1** | 1 | Ethernet | `192.168.5.110` | TG30(1대) 및 GS2(2대) 연동 컨트롤러 |
| **Raspberry Pi 2** | 1 | Ethernet | `192.168.5.111` | TG30(1대) 및 GS2(2대) 연동 컨트롤러 |
| **YDLidar TG30 / GS2** | 6 | USB Serial | N/A | 2D Scan 데이터 수집 (Rpi에 연결됨) |

---

## 5. 패키지 구조 (Package Structure)

```text
w/ (Workspace Root)
│
├── package.xml                 # ROS2 패키지 메타데이터 및 의존성 정의 파일
├── README.md                   # 프로젝트 설명 및 사용법이 작성된 마크다운 문서 (본 파일)
├── setup.cfg                   # 스크립트 설치 경로 및 환경 설정 파일
├── setup.py                    # 패키지 빌드, 데이터 파일 전송 및 엔트리 포인트 정의 스크립트
│
├── lidar_control/              # 소스코드 및 런치 파일 통합 상위 디렉토리
│   ├── launch/                 # 시스템 자동 구동을 위한 런치 스크립트 폴더
│   │   ├── foxglove_launch.py  # Foxglove WebSocket 브리지 및 통합 데이터 송출 실행 런치 파일
│   │   └── lidars_launch.py    # 8대 라이다 드라이버 동시 실행 및 정적 TF 브로드캐스팅 런치 파일
│   │
│   └── lidar_control/          # ROS2 실제 파이썬 소스코드 프로그램 디렉토리
│       ├── __init__.py         # 디렉토리를 파이썬 모듈/패키지로 인식시키기 위한 필수 초기화 파일
│       ├── controller.py       # 전체 센서 노드의 수명 주기 및 상태 관제용 중앙 제어 노드
│       ├── gs2_bypasser.py     # YDLidar GS2 시리얼 데이터를 수신하고 표준 Scan 메시지로 변환하는 노드
│       ├── hummingbird_bypasser.py # Seyond Hummingbird D1 UDP law 데이터를 수신하고 PointCloud2로 중계하는 노드
│       └── tg30_bypasser.py    # YDLidar TG30 시리얼 데이터를 수신하고 표준 Scan 메시지로 변환하는 노드
│
├── resource/                   # ROS2 빌드 인덱스 자원 디렉토리
│   └── lidar_control           # ament_index 시스템이 본 폴더를 공식 ROS2 패키지로 인식하도록 돕는 빈 마커 파일
│
└── Rpi_auto_set/               # 엣지 디바이스(라즈베리 파이) 원격 제어 및 자동화 스크립트 폴더
    └── autoStart.sh            # 라즈베리 파이 부팅 시 백그라운드 엣지 바이패스 노드를 무인 구동하는 쉘 스크립트
```

---

## 6. 전체 설치 순서 (Quick Start)

```text
1. Ubuntu 24.04 설치
2. ROS2 Jazzy 설치
3. D1 SDK 설치 및 IP 설정
4. YDLidar SDK 설치
5. ydlidar_ros2_driver 설치
6. lidar_control 패키지 빌드
7. Netplan 네트워크 설정
8. lidars_launch.py 실행
9. foxglove_launch.py 실행
10. Foxglove Studio 접속
```