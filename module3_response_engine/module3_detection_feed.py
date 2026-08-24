"""
GRID GUARD — Module 3: Automated Detection Feed

Closes the loop that was missing: nothing in Module 2 currently
publishes risk scores on its own -- predictor.py only computes them
on-demand when the Flask dashboard asks. This script periodically
calls Module 2's existing predictor directly (no changes to his
code needed) and publishes each scored flow to channel:risk_updates,
exactly the way Module 2 was always supposed to.

This makes the full pipeline self-driving:
    this feed -> channel:risk_updates -> module3_pipeline.py
    -> decide -> execute -> log -> WebSocket push -> dashboard

Run this as its own process, alongside app.py and module3_pipeline.py:
    python3 module3_response_engine/module3_detection_feed.py

Tune with env vars:
    GRIDGUARD_FEED_INTERVAL_SECONDS (default 10)
    GRIDGUARD_FEED_BATCH_SIZE       (default 5)
"""

import json
import os
import sys
import time

import redis

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'module2_detection', 'webapp'))
from predictor import predictor

REDIS_HOST = os.getenv("GRIDGUARD_REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("GRIDGUARD_REDIS_PORT", "6379"))
RISK_CHANNEL = "channel:risk_updates"
INTERVAL_SECONDS = int(os.getenv("GRIDGUARD_FEED_INTERVAL_SECONDS", "10"))
BATCH_SIZE = int(os.getenv("GRIDGUARD_FEED_BATCH_SIZE", "5"))


def run_feed():
    print("=" * 60)
    print("GRID GUARD — Automated Detection Feed")
    print("=" * 60)

    if not predictor.loaded:
        print("[Feed] Module 2's models aren't loaded. Check data/ and models/ folders.")
        sys.exit(1)

    r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
    r.ping()
    print(f"[Feed] Connected to Redis at {REDIS_HOST}:{REDIS_PORT}")
    print(f"[Feed] Publishing {BATCH_SIZE} scored flows every {INTERVAL_SECONDS}s to '{RISK_CHANNEL}'")
    print("[Feed] Running (Ctrl+C to stop)...\n")

    while True:
        flows = predictor.predict_sample(n=BATCH_SIZE)
        for flow in flows:
            message = {
                "meter_id": flow["flow_id"],
                "risk_score": flow["risk_score"],
            }
            r.publish(RISK_CHANNEL, json.dumps(message))
            print(f"[Feed] Published {message['meter_id']} risk={message['risk_score']:.1f}%")

        time.sleep(INTERVAL_SECONDS)


if __name__ == "__main__":
    try:
        run_feed()
    except redis.exceptions.ConnectionError as e:
        print(f"[Feed] Could not connect to Redis: {e}")
    except KeyboardInterrupt:
        print("\n[Feed] Stopped.")
