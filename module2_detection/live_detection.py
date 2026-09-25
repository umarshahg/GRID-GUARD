import redis
import json
import time
from traffic_analyzer import TrafficAnalyzer

class LiveDetection:
    def __init__(self):
        self.analyzer = TrafficAnalyzer()
        self.redis_client = redis.Redis(host='localhost', port=6379, db=0)
    
    def run(self):
        print("[LiveDetection] Starting with live traffic analysis")
        while True:
            try:
                self.analyzer.capture_traffic()
                risk, tier = self.analyzer.get_risk_score()
                
                alert = {
                    'meter_id': "METER-001",
                    'ip': '10.99.1.1',
                    'risk_score': risk,
                    'tier': tier,
                    'timestamp': time.time()
                }
                
                self.redis_client.publish('channel:risk_updates', json.dumps(alert))
                print(f"[LiveDetection] Published: {tier} - Risk={risk:.1f}%\n")
                time.sleep(1)
            except Exception as e:
                print(f"[LiveDetection] Error: {e}")
                time.sleep(2)

if __name__ == "__main__":
    detector = LiveDetection()
    detector.run()
