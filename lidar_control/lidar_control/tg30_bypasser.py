#!/usr/bin/env python3
import os
import sys
import time
import threading
import select
import numpy as np

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy
from std_msgs.msg import String
from sensor_msgs.msg import LaserScan

import ydlidar





# ================================== Node =====================================
class Bypasser(Node):
    def __init__(self):
        super().__init__('bypasser')

        # ---- Parameters ----
        self.declare_parameter('cmd_topic', '/total_lidar_cmd')
        self.declare_parameter('status_topic', '/tg30/status')
        self.declare_parameter('scan_topic', '/scan')
        self.declare_parameter('serial_port', '/dev/ydlidar')
        self.declare_parameter('baudrate', 512000)
        self.declare_parameter('frame_id', 'laser_frame')
        self.declare_parameter('range_min', 0.01)
        self.declare_parameter('range_max', 50.0)
        self.declare_parameter('scan_frequency', 10.0)
        self.declare_parameter('sample_rate', 9)
        self.declare_parameter('intensity', True)

        self.cmd_topic   = self.get_parameter('cmd_topic').value
        self.status_topic= self.get_parameter('status_topic').value
        self.scan_topic  = self.get_parameter('scan_topic').value
        self.port_param  = self.get_parameter('serial_port').value
        self.baud        = int(self.get_parameter('baudrate').value)
        self.frame_id    = self.get_parameter('frame_id').value
        self.range_min   = float(self.get_parameter('range_min').value)
        self.range_max   = float(self.get_parameter('range_max').value)
        self.scan_freq   = float(self.get_parameter('scan_frequency').value)
        self.sample_rate = int(self.get_parameter('sample_rate').value)
        self.intensity   = bool(self.get_parameter('intensity').value)

        # ---- ROS pub/sub ----
        qos = QoSProfile(depth=5)
        qos.reliability = ReliabilityPolicy.BEST_EFFORT
        qos.history = HistoryPolicy.KEEP_LAST
        self.scan_pub = self.create_publisher(LaserScan, self.scan_topic, qos)
        self.status_pub = self.create_publisher(String, self.status_topic, 10)
        self.create_subscription(String, self.cmd_topic, self.on_cmd, 10)

        # ---- Lidar state ----
        self.laser = None
        self._running = False
        self._thread = None
        self._lock = threading.Lock()

        self._say(f"Bypasser up. listening='{self.cmd_topic}', publishing='{self.scan_topic}', status='{self.status_topic}'")

    # ===== utilities =====
    def _say(self, text: str):
        self.get_logger().info(text)
        self.status_pub.publish(String(data=text))

    def _log(self, text: str):
        self.get_logger().info(text)

    def _pick_port(self):
        if self.port_param and os.path.exists(self.port_param):
            return self.port_param
        ports = ydlidar.lidarPortList()
        for _, v in ports.items():
            return v
        return None

    # ===== command handling =====
    def on_cmd(self, msg: String):
        c = (msg.data or '').strip().lower()
        if c == 's':
            self.start_scan()
        elif c == 'p':
            self.stop_scan()
        elif c == 'q':
            self.stop_scan()
            self._say("Quit command received.")
            rclpy.shutdown()
        else:
            self._say(f"Unknown cmd '{msg.data}' (expected s/p/g/q).")

    # ===== start/stop & publish scans =====
    def start_scan(self):
        with self._lock:
            if self._running:
                self._say("Already scanning.")
                return
            port = self._pick_port()
            if not port:
                self._say("No YDLidar serial port found.")
                return

            self.laser = ydlidar.CYdLidar()
            self.laser.setlidaropt(ydlidar.LidarPropSerialPort, port)
            self.laser.setlidaropt(ydlidar.LidarPropSerialBaudrate, self.baud)
            self.laser.setlidaropt(ydlidar.LidarPropLidarType, ydlidar.TYPE_TRIANGLE)
            self.laser.setlidaropt(ydlidar.LidarPropDeviceType, ydlidar.YDLIDAR_TYPE_SERIAL)
            self.laser.setlidaropt(ydlidar.LidarPropSingleChannel, True)
            try: self.laser.setlidaropt(ydlidar.LidarPropScanFrequency, float(self.scan_freq))
            except Exception: pass
            try: self.laser.setlidaropt(ydlidar.LidarPropSampleRate, int(self.sample_rate))
            except Exception: pass
            self.laser.setlidaropt(ydlidar.LidarPropMaxAngle, 180.0)
            self.laser.setlidaropt(ydlidar.LidarPropMinAngle, -180.0)
            self.laser.setlidaropt(ydlidar.LidarPropMaxRange, float(self.range_max))
            self.laser.setlidaropt(ydlidar.LidarPropMinRange, float(self.range_min))

            if not self.laser.initialize():
                self._say("initialize() failed.")
                self.laser = None
                return
            if not self.laser.turnOn():
                self._say("turnOn() failed.")
                try: self.laser.turnOff()
                except Exception: pass
                self.laser = None
                return

            self._running = True
            self._thread = threading.Thread(target=self._scan_loop, daemon=True)
            self._thread.start()
            self._say(f"Started scanning on {port}@{self.baud}.")

    def stop_scan(self):
        with self._lock:
            if not self._running:
                self._say("Already stopped.")
                return
            self._running = False

        if self._thread:
            self._thread.join(timeout=2.0)
            self._thread = None

        with self._lock:
            if self.laser:
                try:
                    self.laser.turnOff()
                except Exception:
                    pass
                try:
                    self.laser.disconnecting()
                except Exception:
                    pass
                self.laser = None

        self._say("Stopped scanning.")

    def _scan_loop(self):
        scan = ydlidar.LaserScan()
        while True:
            with self._lock:
                if not self._running:
                    break

            ok = self.laser.doProcessSimple(scan)
            if not ok:
                time.sleep(0.003)
                continue

            # Preferred layout: scan.points list with angle/range/intensity
            if hasattr(scan, "points") and scan.points is not None:
                angles = [pt.angle for pt in scan.points]
                ranges = [pt.range for pt in scan.points]
                intens = [getattr(pt, "intensity", 0.0) for pt in scan.points]
                if not angles:
                    continue
                angles = np.array(angles, dtype=float)
                ranges = np.array(ranges, dtype=float)
                intens = np.array(intens, dtype=float)

                order = np.argsort(angles)
                angles = angles[order]; ranges = ranges[order]; intens = intens[order]
                # degrees vs radians heuristic
                theta = np.deg2rad(angles) if (angles.max() - angles.min() > 6.5) else angles
                n = len(theta)
                ang_inc = float(np.median(np.diff(theta))) if n > 1 else 0.0

                msg = LaserScan()
                msg.header.stamp = self.get_clock().now().to_msg()
                msg.header.frame_id = self.frame_id
                msg.angle_min = float(theta[0])
                msg.angle_max = float(theta[-1])
                msg.angle_increment = float(ang_inc)
                msg.time_increment = 0.0
                msg.scan_time = 0.0
                msg.range_min = float(self.range_min)
                msg.range_max = float(self.range_max)
                msg.ranges = ranges.tolist()
                msg.intensities = intens.tolist()
                self.scan_pub.publish(msg)
            else:
                # Fallback: some wrappers put fields under scan.config / scan.ranges
                if hasattr(scan, "ranges") and hasattr(scan, "config"):
                    n = len(scan.ranges)
                    if n == 0:
                        continue
                    min_a = float(getattr(scan.config, "min_angle", -np.pi))
                    inc   = float(getattr(scan.config, "angle_increment", (2*np.pi)/max(1,n)))
                    msg = LaserScan()
                    msg.header.stamp = self.get_clock().now().to_msg()
                    msg.header.frame_id = self.frame_id
                    msg.angle_min = min_a
                    msg.angle_max = min_a + inc * (n - 1)
                    msg.angle_increment = inc
                    msg.time_increment = float(getattr(scan.config, "time_increment", 0.0))
                    msg.scan_time = float(getattr(scan.config, "scan_time", 0.0))
                    msg.range_min = float(self.range_min)
                    msg.range_max = float(self.range_max)
                    msg.ranges = list(scan.ranges)
                    msg.intensities = list(getattr(scan, "intensities", [])) if hasattr(scan, "intensities") else []
                    self.scan_pub.publish(msg)

def main():
    rclpy.init()
    node = Bypasser()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.stop_scan()
        node.destroy_node()
        rclpy.shutdown()

if __name__ == "__main__":
    main()