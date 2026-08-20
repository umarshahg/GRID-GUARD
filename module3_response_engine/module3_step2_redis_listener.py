"""
GRID GUARD — Module 3: Graduated Response Engine
STEP 2: Redis Alert Listener

Subscribes to the Redis pub/sub channel that Module 2 publishes
risk scores to (per SDS Table 3.9: channel:risk_updates), and
feeds every incoming (meter_id, risk_score) pair into the
GraduatedResponseEngine from Step 1.

This step only LISTENS + DECIDES. It does not yet execute actions
(iptables, alerts in DB, isolation) or persist anything — that's
Step 3 onward. Right now it just proves the pipe from Redis to the
decision engine works end-to-end.

Requires: pip install redis
"""

import json
import os
import sys

import redis

sys.path.append(os.path.dirname(__file__))
from module3_step1_response_engine import GraduatedResponseEngine

# ── Config ──────────────────────────────────────────────────────
REDIS_HOST = os.getenv("GRIDGUARD_REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("GRIDGUARD_REDIS_PORT", "6379"))
RISK_CHANNEL = "channel:risk_updates"


class RedisAlertListener:
    """
    Listens on channel:risk_updates for messages published by
    Module 2's Detection Engine, and runs each one through the
    Graduated Response Engine.

    Expected message format (JSON):
        {"meter_id": "SM-1234", "risk_score": 87.5}
    """

    def __init__(self):
        self.redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
        self.engine = GraduatedResponseEngine()
        self.pubsub = self.redis_client.pubsub()

    def start(self):
        print(f"[Listener] Connecting to Redis at {REDIS_HOST}:{REDIS_PORT} ...")
        self.redis_client.ping()  # raises if Redis isn't reachable
        print(f"[Listener] Connected. Subscribing to '{RISK_CHANNEL}' ...")

        self.pubsub.subscribe(RISK_CHANNEL)
        print("[Listener] Waiting for risk score events (Ctrl+C to stop)...\n")

        for message in self.pubsub.listen():
            if message["type"] != "message":
                continue  # skip the subscribe confirmation event
            self._handle_message(message["data"])

    def _handle_message(self, raw_data: str):
        try:
            payload = json.loads(raw_data)
            meter_id = payload["meter_id"]
            risk_score = float(payload["risk_score"])
        except (json.JSONDecodeError, KeyError, TypeError, ValueError) as e:
            print(f"[Listener] ⚠️  Skipping malformed message: {raw_data!r} ({e})")
            return

        decision = self.engine.decide_response(meter_id, risk_score)
        print(
            f"[Listener] {decision.meter_id} | risk={decision.risk_score:.1f}% "
            f"-> Tier {decision.tier.value} ({decision.action.value}) | {decision.description}"
        )
        return decision


if __name__ == "__main__":
    listener = RedisAlertListener()
    try:
        listener.start()
    except redis.exceptions.ConnectionError as e:
        print(f"[Listener] ❌ Could not connect to Redis: {e}")
        print("[Listener] Is Redis running? Try: redis-server (or `docker run -p 6379:6379 redis`)")
    except KeyboardInterrupt:
        print("\n[Listener] Stopped.")
