import socket
import time
import random
import struct

class MeterSimulator:
    def __init__(self, port=4059):
        self.port = port
        self.running = True
    
    def simulate_normal_traffic(self):
        """Normal meter consumption pattern"""
        return struct.pack('!I', random.randint(100, 150))  # 100-150kWh
    
    def simulate_anomaly_traffic(self):
        """Suspicious pattern - rapid requests"""
        packets = []
        for _ in range(10):
            packets.append(struct.pack('!I', random.randint(500, 1000)))
        return b''.join(packets)
    
    def run(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(('0.0.0.0', self.port))
        sock.listen(5)
        print(f"[Meter] Listening on port {self.port}")
        
        anomaly_mode = False
        anomaly_timer = 0
        
        while True:
            try:
                conn, addr = sock.accept()
                print(f"[Meter] Connection from {addr}")
                
                # Simulate normal traffic 80% of time, anomalies 20%
                if random.random() > 0.8:
                    anomaly_mode = True
                    anomaly_timer = 5
                
                if anomaly_mode and anomaly_timer > 0:
                    data = self.simulate_anomaly_traffic()
                    anomaly_timer -= 1
                else:
                    anomaly_mode = False
                    data = self.simulate_normal_traffic()
                
                conn.send(data)
                conn.close()
                time.sleep(random.uniform(0.5, 2))
            except Exception as e:
                print(f"[Meter] Error: {e}")

if __name__ == "__main__":
    meter = MeterSimulator()
    meter.run()
