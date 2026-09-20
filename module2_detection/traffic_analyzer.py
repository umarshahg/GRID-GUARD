import socket
import time
import random
from collections import deque
import numpy as np

class TrafficAnalyzer:
    def __init__(self, port=4059):
        self.port = port
        self.packet_sizes = deque(maxlen=5)  # Keep only last 5 packets
    
    def capture_traffic(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.connect(('localhost', self.port))
            data = sock.recv(16384)
            self.packet_sizes.append(len(data))
            print(f"[Capture] Received {len(data)}B | Recent packets: {list(self.packet_sizes)}")
            return len(data)
        except:
            return 0
        finally:
            sock.close()
    
    def get_risk_score(self):
        if not self.packet_sizes:
            return 0, "No data"
        
        max_size = max(self.packet_sizes)
        avg_size = np.mean(list(self.packet_sizes))
        print(f"[Analysis] max={max_size}B | avg={avg_size:.0f}B")
        
        # Risk based on packet size
        if max_size < 150:
            risk = random.uniform(5, 35)
            tier = "Tier 1 (Normal: 5-35%)"
        elif max_size < 500:
            risk = random.uniform(40, 80)
            tier = "Tier 2 (Suspicious: 40-80%)"
        elif max_size < 5000:
            risk = random.uniform(80, 95)
            tier = "Tier 3 (Anomaly: 80-95%)"
        else:
            risk = random.uniform(95, 100)
            tier = "Tier 4 (Attack: 95-100%)"
        
        # RESET deque so previous packets don't affect next calculation
        self.packet_sizes.clear()
        
        return risk, tier
