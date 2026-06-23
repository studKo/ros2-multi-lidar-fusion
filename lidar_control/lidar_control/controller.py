#!/usr/bin/env python3
import threading
import time
import rclpy
from rclpy.node import Node
from std_msgs.msg import String

HELP = """\
Commands:
  s = start scan
  p = stop/pause (ignored if not started)
  g = current device info (via getDeviceInfo)
  q = stop (if running) and quit
"""

class Controller(Node):
    def __init__(self):
        super().__init__('controller')
        self.declare_parameter('cmd_topic', '/total_lidar_cmd')
        self.declare_parameter('status_topic', '/total_lidar_status')
        self.cmd_topic = self.get_parameter('cmd_topic').value
        self.status_topic = self.get_parameter('status_topic').value
        
        self.pub = self.create_publisher(String, self.cmd_topic, 10)
        self.create_subscription(String, self.status_topic, self.on_status, 10)
        
        self._scanning = False
        self.get_logger().info(
            f"Controller ready.\n- send on {self.cmd_topic}\n- read from {self.status_topic}"
        )
        print(HELP)
        self._stop_reader = False
        self._reader = threading.Thread(target=self._read_stdin_loop, daemon=True)
        self._reader.start()
        
    def on_status(self, msg: String):
        text = msg.data or ""
        print(f"[status] {text}")
        if "Started scanning" in text:
            self._scanning = True
        elif "Stopped scanning" in text or "Already stopped" in text:
            self._scanning = False
            
    def send(self, c: str):
        c = (c or '').strip().lower()
        if c not in ('s', 'p', 'g'):
            print("unknown command; valid: s p g q"); return
        if c == 'p' and not self._scanning:
            print("Not scanning; 'p' ignored. Start with 's'."); return
        self.pub.publish(String(data=c))
        self.get_logger().info(f"sent '{c}'")
        if c == 's': self._scanning = True
        elif c == 'p': self._scanning = False
        
    def _read_stdin_loop(self):
        try:
            while not self._stop_reader:
                try:
                    line = input("> ").strip().lower()
                except EOFError:
                    break
                if not line: continue
                cmd = line[0]
                if cmd == 'q':
                    if self._scanning:
                        self.send('p'); time.sleep(0.2)
                    print("bye."); rclpy.shutdown(); break
                if cmd in ('s','p','g'): self.send(cmd)
                else: print("valid: s p g q")
        except Exception as e:
            self.get_logger().warn(f"stdin loop error: {e}")
            
def main():
    rclpy.init()
    node = Controller()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node._stop_reader = True
        node.destroy_node()
        if rclpy.ok(): rclpy.shutdown()
        
if __name__ == "__main__":
    main()