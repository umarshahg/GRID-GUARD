"""
Module 3 Detection Feed - Simplified
Publishes synthetic risk scores across all tiers
"""

import json
import redis
import random
import time
from datetime import datetime

def publish_risk_scores():
    """Publish risk scores to Redis, covering all tiers."""
    try:
        r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
        r.ping()
        print("[Feed] Connected to Redis at localhost:6379")
    except Exception as e:
        print(f"[Feed] ❌ Redis connection failed: {e}")
        return

    print("[Feed] Publishing 5 scored flows every 10s to 'channel:risk_updates'")
    print("[Feed] Tier distribution: LOG(0-40%), ALERT(40-80%), RATE_LIMIT(80-95%), ISOLATION(95-100%)")
    print("[Feed] Running (Ctrl+C to stop)...\n")

    meter_ids = [f"FLOW-{i:04d}" for i in range(1, 6)]
    ip_range = lambda i: f"10.99.{i % 255}.{(i*7) % 255}"

    try:
        while True:
            for i, meter_id in enumerate(meter_ids):
                # Pick a random tier
                tier_choice = random.random()
                if tier_choice < 0.40:
                    risk_score = random.uniform(0, 40)        # Tier 1: LOG
                elif tier_choice < 0.80:
                    risk_score = random.uniform(40, 80)       # Tier 2: ALERT
                elif tier_choice < 0.95:
                    risk_score = random.uniform(80, 95)       # Tier 3: RATE_LIMIT
                else:
                    risk_score = random.uniform(95, 100)      # Tier 4: ISOLATION

                alert = {
                    'meter_id': meter_id,
                    'ip': ip_range(i),
                    'risk_score': risk_score,
                    'timestamp': datetime.utcnow().isoformat() + 'Z'
                }

                r.publish('channel:risk_updates', json.dumps(alert))
                print(f"[Feed] Published {meter_id} risk={risk_score:.1f}%")

            time.sleep(10)

    except KeyboardInterrupt:
        print("\n[Feed] Stopped.")
    except Exception as e:
        print(f"[Feed] ❌ Error: {e}")

if __name__ == "__main__":
    publish_risk_scores()
