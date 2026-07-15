# ROS2 Multi-LiDAR Fusion and Visualization System

![ROS2](https://img.shields.io/badge/ROS2-Jazzy-22314E?logo=ros)
![Ubuntu](https://img.shields.io/badge/Ubuntu-24.04-E95420?logo=ubuntu)

## 0. 사전 준비 (Pre-Installation)

### 0.1 물리적 연결 구성 (Physical Connection Setup)

설치를 진행하기 전, 아래의 사전 연결 구성도를 참고하여 각 센서와 Raspberry Pi, 호스트 서버 간의 물리적 배선을 완료해야 합니다.

- Ubuntu 24.04 Desktop이 설치된 호스트 서버 준비
- Hummingbird D1 x2, Raspberry Pi x2(TG30/GS2 연동 컨트롤러) 이더넷 연결
- YDLidar TG30 / GS2는 USB Serial로 각 Raspberry Pi에 연결

> 상세 배선도는 별도 첨부된 "사전 연결 구성도" 문서를 참고하세요.

---

## 1. 센서 드라이버 설치 및 초기 설정 (Sensor Driver Installation & Initial Setup)

### 1.1 ROS2 Jazzy 설치 (Ubuntu 24.04)

아래 명령어를 실행하여 ROS2가 이미 설치되어 있는지 먼저 확인합니다. 아무것도 출력되지 않으면 아래 설치 절차를 진행합니다.

```bash
which ros2
```

```bash
# 시스템 업데이트
sudo apt update
sudo apt upgrade -y

sudo reboot
```

```bash
# Locale 설정
sudo apt install locales
sudo locale-gen en_US en_US.UTF-8
sudo update-locale LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8
export LANG=en_US.UTF-8
```

```bash
# Universe Repository 활성화
sudo apt install software-properties-common -y
sudo add-apt-repository universe -y

sudo apt update
sudo apt install curl gnupg lsb-release -y
```

```bash
# ROS Key 등록
sudo curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key \
-o /usr/share/keyrings/ros-archive-keyring.gpg
```

```bash
# Repository 등록
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] http://packages.ros.org/ros2/ubuntu $(. /etc/os-release && echo $UBUNTU_CODENAME) main" | sudo tee /etc/apt/sources.list.d/ros2.list > /dev/null
sudo apt update
```

```bash
# ROS2 Jazzy 설치
sudo apt install ros-jazzy-desktop -y
```

```bash
# 환경 변수 설정
source /opt/ros/jazzy/setup.bash

# 환경 변수 자동화 설정
echo "source /opt/ros/jazzy/setup.bash" >> ~/.bashrc
source ~/.bashrc
```

```bash
# 설치된 ROS2 버전 확인
printenv | grep ROS

ros2 doctor
```

```bash
# 설정 파일을 실행한 다음 C++ 예제를 확인할 수 있습니다.
ros2 run demo_nodes_cpp talker
# 작동 확인 후 Ctrl + C 를 눌러 종료하세요
```

---

### 1.2 Seyond Hummingbird D1 Client SDK 및 ROS2 Driver 설치

Hummingbird D1 센서를 사용하기 위해서는 공식 Client SDK 설치, ROS2 Driver 설치, 그리고 센서 IP/MAC 설정이 필요합니다.

#### 1) 작업 폴더 생성 및 파일 준비

```bash
mkdir -p ~/SEYOND_SDK
cd ~/SEYOND_SDK
```

다운로드한 아래 두 개의 파일을 작업 폴더(`~/SEYOND_SDK`)로 이동합니다.

| 파일 | 용도 |
| :--- | :--- |
| `inno-lidar-sdk-release-client-sdk-3.103.7-public.tgz` | LiDAR Client SDK 및 센서 설정 도구 |
| `seyond-ros2-jazzy-3.103.7-rv3.6.5-x86.deb` (ros-seyond.zip 내부) | ROS2 Driver |

#### 2) Client SDK 압축 해제 및 빌드

```bash
# Client SDK 압축 해제
tar -xzf inno-lidar-sdk-release-client-sdk-3.103.7-public.tgz
cd ~/SDK_file_path
```

드라이버 폴더에서 빌드 스크립트를 실행합니다.

```bash
./build.sh
```

#### 3) ROS2 Driver 설치

```bash
# unzip 패키지 설치 확인 및 ROS2 Driver 압축 해제
sudo apt install unzip -y
unzip ros-seyond.zip
# 압축 해제 후 ros-seyond/ 폴더가 생성됩니다.

# ROS2 Driver 설치
sudo apt install ./ros-seyond/seyond-ros2-jazzy-3.103.7-rv3.6.5-x86.deb -y
```

만약 설치 중 의존성 오류가 발생하면 아래 명령어 실행 후 드라이버 설치 명령어를 다시 입력하세요.

```bash
sudo apt --fix-broken install -y
```

```bash
# 설치 확인
dpkg -l | grep seyond
```

#### 4) 센서 네트워크(IP) 설정

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

변경 사항 적용을 위해 소프트 재부팅 후 통신 테스트를 진행합니다.

```bash
# 라이다 소프트 재부팅 (변경 사항 적용)
./innovusion_lidar_util 172.168.1.10 soft_reboot

# 변경 테스트
ping -c 3 192.168.5.101
```

#### 5) 센서 MAC 주소 변경

기존 기기는 기기별로 동일한 IP와 MAC 주소를 보유하고 있기 때문에, IP뿐 아니라 MAC 주소도 함께 변경해야 합니다. 아래 절차에 필요한 `mac_change.py` 파일을 준비하고, 해당 파일이 있는 경로에서 터미널을 엽니다.

```bash
python mac_change.py --lidar-ip 192.168.5.101 --mac 04:C3:E6:46:23:CF
```

```bash
echo "flash_wr 0x21 0x04" | nc -nv 192.168.5.101 8002 -q 1
```

라이다를 재부팅하여 변경 사항을 적용합니다.

```bash
echo reboot 1 | nc -nv 192.168.5.101 8002
```

---

### 1.3 YDLidar SDK 및 ROS2 Driver 설치

TG30 및 GS2 센서를 사용하기 위해서는 YDLidar SDK와 ROS2 드라이버 설치가 필요합니다.

#### 1) YDLidar SDK 설치

```bash
git clone https://github.com/YDLIDAR/YDLidar-SDK.git

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

git clone https://github.com/YDLIDAR/ydlidar_ros2_driver.git
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

### 1.4 Foxglove 및 Foxglove Bridge 설치

만약 이미 설치되어 있다면 다음 단계로 진행합니다.

```bash
# Foxglove Bridge 설치
sudo apt install ros-jazzy-foxglove-bridge -y

# 설치 확인 및 브릿지 노드 실행 테스트
ros2 run foxglove_bridge foxglove_bridge
```

Foxglove Studio(뷰어)는 브라우저를 통해 공식 사이트에 직접 방문하여 환경에 맞는 버전을 다운로드/설치하는 것을 권장합니다.

- Download: [Foxglove 공식 다운로드 페이지](https://foxglove.dev/download)

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
│       ├── hummingbird_bypasser.py # Seyond Hummingbird D1 UDP raw 데이터를 수신하고 PointCloud2로 중계하는 노드
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
1. Ubuntu 24.04 설치 및 물리적 연결 구성 확인
2. ROS2 Jazzy 설치 (1.1)
3. Seyond Client SDK 및 ROS2 Driver 설치, IP/MAC 설정 (1.2)
4. YDLidar SDK 및 ROS2 Driver 설치 (1.3)
5. Foxglove / Foxglove Bridge 설치 (1.4)
6. lidar_control 패키지 빌드
7. Netplan 네트워크 설정
8. lidars_launch.py 실행
9. foxglove_launch.py 실행
10. Foxglove Studio 접속
```
