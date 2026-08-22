"""
GRID GUARD — Module 3: Graduated Response Engine
LIVE PIPELINE — connects Step 2 (listen) -> Step 1 (decide) ->
Step 3 (execute) -> Step 4 (log to DB) into one continuous process.

This is what actually makes FE-1 through FE-4 "live" instead of
something you have to trigger manually with test scripts. Run this
once, alongside Module 2's detection service, and every risk score
Module 2 publishes gets decided, executed, and logged automatically.

Run:
    python3 module3_response_engine/module3_pipeline.py

Requires: redis-server and PostgreSQL both running, and the
audit_log table already created (you've done both).
"""

import json
import os
import sys

import redis

sys.path.append(os.path.dirname(__file__))
from module3_step1_response_engine import GraduatedResponseEngine
from module3_step3_action_executor import ActionExecutor
from module3_step4_database_logger import DatabaseLogger

REDIS_HOST = os.getenv("GRIDGUARD_REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("GRIDGUARD_REDIS_PORT", "6379"))
RISK_CHANNEL = "channel:risk_updates"


class ResponsePipeline:
    """
    Wires the four Module 3 steps together:
      Redis message -> decide_response() -> execute() -> log_decision()
    """

    def __init__(self):
        self.engine = GraduatedResponseEngine()
        self.executor = ActionExecutor()
        self.logger = DatabaseLogger()
        self.redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
        self.pubsub = self.redis_client.pubsub()

    def start(self):
        print("=" * 60)
        print("GRID GUARD — Module 3 Live Pipeline")
        print("=" * 60)

        if not self.logger.connect():
            print("[Pipeline] Could not connect to PostgreSQL. Exiting.")
            sys.exit(1)

        print(f"[Pipeline] Connecting to Redis at {REDIS_HOST}:{REDIS_PORT} ...")
        self.redis_client.ping()
        print(f"[Pipeline] Subscribing to '{RISK_CHANNEL}' ...")
        self.pubsub.subscribe(RISK_CHANNEL)
        print("[Pipeline] Ready. Waiting for risk score events (Ctrl+C to stop)...\n")

        for message in self.pubsub.listen():
            if message["type"] != "message":
                continue
            self._handle(message["data"])

    def _handle(self, raw_data: str):
        try:
            payload = json.loads(raw_data)
            meter_id = payload["meter_id"]
            risk_score = float(payload["risk_score"])
        except (json.JSONDecodeError, KeyError, TypeError, ValueError) as e:
            print(f"[Pipeline] Skipping malformed message: {raw_data!r} ({e})")
            return

        # Step 1: decide
        decision = self.engine.decide_response(meter_id, risk_score)
        print(f"[Pipeline] {decision.meter_id} risk={decision.risk_score:.1f}% "
              f"-> Tier {decision.tier.value} ({decision.action.value})")

        # Step 3: execute
        self.executor.execute(decision)

        # Step 4: log to DB (this is what makes it show up on /ids-ips)
        self.logger.log_decision(decision)
        self.logger.insert_alert(decision)

if __name__ == "__main__":
    pipeline = ResponsePipeline()
    try:
        pipeline.start()
    except redis.exceptions.ConnectionError as e:
        print(f"[Pipeline] Could not connect to Redis: {e}")
    except KeyboardInterrupt:
        print("\n[Pipeline] Stopped.")
        pipeline.logger.close()
