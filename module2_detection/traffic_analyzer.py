import socket
import time
import random
from collections import deque
import numpy as np

class TrafficAnalyzer:
    def __init__(self, port=4059, window_size=30):
        self.port = port
        self.window_size = window_size
        self.packet_sizes = deque(maxlen=window_size)
        self.packet_times = deque(maxlen=window_size)
    
    def capture_traffic(self):
        """Capture traffic from meter"""
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.connect(('localhost', self.port))
            data = sock.recv(4096)
            current_time = time.time()
            
            self.packet_sizes.append(len(data))
            self.packet_times.append(current_time)
            
            return len(data), current_time
        finally:
            sock.close()
    
    def extract_features(self):
        """Extract features"""
        if len(self.packet_sizes) < 2:
            return np.zeros(5)
        
        packet_count = len(self.packet_sizes)
        total_bytes = sum(self.packet_sizes)
        avg_size = np.mean(self.packet_sizes)
        
        times = list(self.packet_times)
        if len(times) > 1:
            intervals = [times[i+1] - times[i] for i in range(len(times)-1)]
            timing_variance = np.std(intervals) if intervals else 0
        else:
            timing_variance = 0
        
        return np.array([
            packet_count,
            total_bytes,
            avg_size,
            timing_variance * 100,
            len([t for t in times if time.time() - t < 5])
        ])
    
    def get_anomaly_score(self, features):
        """Calculate risk from 0-100 across all tiers"""
        packet_count = features[0]
        total_bytes = features[1]
        avg_size = features[2]
        
        risk = 0
        
        if avg_size < 100:
            risk += 10
        elif avg_size < 250:
            risk += 40
        elif avg_size < 600:
            risk += 75
        else:
            risk += 98
        
        if packet_count > 20:
            risk = min(risk + 30, 100)
        
        if total_bytes > 2000:
            risk = min(risk + 20, 100)
        
        tier_variance = random.uniform(-5, 5)
        risk = min(max(risk + tier_variance, 0), 100)
        
        return risk
