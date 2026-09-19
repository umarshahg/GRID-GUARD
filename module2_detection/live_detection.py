import redis
import json
import time
from traffic_analyzer import TrafficAnalyzer

class LiveDetection:
    def __init__(self):
        self.analyzer = TrafficAnalyzer()
        self.redis_client = redis.Redis(host='localhost', port=6379, db=0)
        self.meter_id = "METER-001"
    
    def run(self):
        print("[LiveDetection] Starting live risk detection")
        
        while True:
            try:
                # Get real traffic
                size, ts = self.analyzer.capture_traffic()
                
                # Extract features
                features = self.analyzer.extract_features()
                
                # Calculate risk
                risk_score = self.analyzer.get_anomaly_score(features)
                
                # Publish to Module 3
                alert = {
                    'meter_id': self.meter_id,
                    'ip': '10.99.1.1',
                    'risk_score': risk_score,
                    'timestamp': ts,
                    'features': {
                        'packet_count': float(features[0]),
                        'total_bytes': float(features[1]),
                        'avg_packet_size': float(features[2]),
                        'timing_variance': float(features[3]),
                        'request_frequency': float(features[4])
                    }
                }
                
                self.redis_client.publish('channel:risk_updates', json.dumps(alert))
                print(f"[LiveDetection] {self.meter_id}: Risk={risk_score:.1f}%")
                
                time.sleep(2)
            except Exception as e:
                print(f"[LiveDetection] Error: {e}")
                time.sleep(3)

if __name__ == "__main__":
    detector = LiveDetection()
    detector.run()
