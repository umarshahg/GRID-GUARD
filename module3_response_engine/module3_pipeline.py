"""
GRID GUARD — Module 3: Graduated Response Engine
LIVE PIPELINE — Steps 1-4 plus FE-5 Redis state caching, plus
per-channel delivery status (email_sent/webhook_sent) and real
iptables rate-limit status (rate_limit_ip/rate_limit_applied)
tracking.
"""

import json
import os
import sys

import redis

sys.path.append(os.path.dirname(__file__))
from module3_step1_response_engine import GraduatedResponseEngine
from module3_step3_action_executor import ActionExecutor
from module3_step4_database_logger import DatabaseLogger
from redis_state_manager import RedisStateManager

REDIS_HOST = os.getenv("GRIDGUARD_REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("GRIDGUARD_REDIS_PORT", "6379"))
RISK_CHANNEL = "channel:risk_updates"
DASHBOARD_CHANNEL = "channel:alerts"
TIER_TO_STATE = {1: "NORMAL", 2: "ALERT", 3: "RATE_LIMITED", 4: "SANDBOXED"}


class ResponsePipeline:
    def __init__(self):
        self.engine = GraduatedResponseEngine()
        self.executor = ActionExecutor()
        self.logger = DatabaseLogger()
        self.state_manager = RedisStateManager()
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

        decision = self.engine.decide_response(meter_id, risk_score)
        print(f"[Pipeline] {decision.meter_id} risk={decision.risk_score:.1f}% "
              f"-> Tier {decision.tier.value} ({decision.action.value})")

        execution_result = self.executor.execute(decision)

        self.logger.log_decision(
            decision,
            email_sent=execution_result.get("email_sent"),
            webhook_sent=execution_result.get("webhook_sent"),
            rate_limit_ip=execution_result.get("rate_limit_ip"),
            rate_limit_applied=execution_result.get("rate_limit_applied"),
        )
        self.logger.insert_alert(decision)

        notification = {
            "meter_id": decision.meter_id,
            "risk_score": decision.risk_score,
            "tier": decision.tier.value,
            "action": decision.action.value,
            "description": decision.description,
            "email_sent": execution_result.get("email_sent"),
            "webhook_sent": execution_result.get("webhook_sent"),
            "rate_limit_ip": execution_result.get("rate_limit_ip"),
            "rate_limit_applied": execution_result.get("rate_limit_applied"),
        }
        self.redis_client.publish(DASHBOARD_CHANNEL, json.dumps(notification))

        self.state_manager.update_meter_state(
            meter_id=meter_id,
            tier=decision.action.value,
            risk_score=decision.risk_score / 100,
            details={"description": decision.description},
        )
        self.state_manager.cache_risk_score(meter_id, decision.risk_score / 100, ttl_seconds=90)

        if decision.action.value == "FULL_ISOLATION":
            self.state_manager.mark_meter_isolated(meter_id)
            print(f"[Pipeline] Marked {meter_id} as isolated")


if __name__ == "__main__":
    pipeline = ResponsePipeline()
    try:
        pipeline.start()
    except redis.exceptions.ConnectionError as e:
        print(f"[Pipeline] Could not connect to Redis: {e}")
    except KeyboardInterrupt:
        print("\n[Pipeline] Stopped.")
        pipeline.logger.close()
