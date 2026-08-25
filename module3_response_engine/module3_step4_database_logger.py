"""
GRID GUARD — Module 3: Graduated Response Engine
STEP 4: Database Logger

Takes ResponseDecision from Step 3 and SAVES it to PostgreSQL
audit_log table so the Dashboard can display what actions were taken.

Stores to audit_log table with fields:
  - log_id (auto-increment)
  - meter_id
  - action_type (LOG, ALERT, RATE_LIMIT, FULL_ISOLATION)
  - risk_score
  - description
  - email_sent / webhook_sent (NULL if not applicable, e.g. Tier 1)
  - rate_limit_ip / rate_limit_applied (NULL unless Tier 3)
  - created_at (timestamp)

IMPORTANT: every read method explicitly commits after its query.
psycopg2 connections default to autocommit=False, so even a plain
SELECT opens a transaction that must be closed with commit() or
rollback() -- otherwise it sits "idle in transaction" forever and
can block schema changes (ALTER TABLE) on this table indefinitely.

Requires: pip install psycopg2-binary
"""

import os
import sys
from datetime import datetime
from typing import Optional

import psycopg2
from psycopg2.extras import execute_values

sys.path.append(os.path.dirname(__file__))
from module3_step1_response_engine import ResponseDecision, ResponseAction


class DatabaseLogger:
    def __init__(self):
        self.db_host = os.getenv("DB_HOST", "localhost")
        self.db_port = os.getenv("DB_PORT", "5432")
        self.db_name = os.getenv("DB_NAME", "gridguard")
        self.db_user = os.getenv("DB_USER", "gridguard")
        self.db_password = os.getenv("DB_PASSWORD", "gridguard")
        self.conn = None
        self.connected = False

    def connect(self) -> bool:
        try:
            self.conn = psycopg2.connect(
                host=self.db_host,
                port=self.db_port,
                database=self.db_name,
                user=self.db_user,
                password=self.db_password,
            )
            self.connected = True
            print(f"[DatabaseLogger] ✅ Connected to PostgreSQL {self.db_host}")
            return True
        except psycopg2.Error as e:
            print(f"[DatabaseLogger] ❌ Failed to connect: {e}")
            self.connected = False
            return False

    def log_decision(self, decision: ResponseDecision, email_sent: bool = None, webhook_sent: bool = None,
                      rate_limit_ip: str = None, rate_limit_applied: bool = None) -> bool:
        if not self.connected:
            print(f"[DatabaseLogger] ❌ Not connected to database")
            return False

        try:
            with self.conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO audit_log 
                    (actor, action_type, target_entity, payload, email_sent, webhook_sent, rate_limit_ip, rate_limit_applied, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW())
                    """,
                    (
                        "Module3",
                        decision.action.value,
                        decision.meter_id,
                        str(decision.to_dict()),
                        email_sent,
                        webhook_sent,
                        rate_limit_ip,
                        rate_limit_applied,
                    ),
                )
            self.conn.commit()
            print(f"[DatabaseLogger] ✅ Logged {decision.action.value} for {decision.meter_id} "
                  f"(risk={decision.risk_score}%, email_sent={email_sent}, webhook_sent={webhook_sent}, "
                  f"rate_limit_ip={rate_limit_ip}, rate_limit_applied={rate_limit_applied})")
            return True

        except psycopg2.Error as e:
            print(f"[DatabaseLogger] ❌ Database error: {e}")
            self.conn.rollback()
            return False
        except Exception as e:
            print(f"[DatabaseLogger] ❌ Error: {e}")
            return False

    def log_batch(self, decisions: list) -> int:
        if not self.connected:
            print(f"[DatabaseLogger] ❌ Not connected to database")
            return 0
        success_count = 0
        for decision in decisions:
            if self.log_decision(decision):
                success_count += 1
        print(f"[DatabaseLogger] ✅ Logged {success_count}/{len(decisions)} decisions")
        return success_count

    def get_recent_actions(self, limit: int = 50) -> list:
        if not self.connected:
            print(f"[DatabaseLogger] ❌ Not connected to database")
            return []
        try:
            with self.conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT log_id, actor, action_type, target_entity, payload, email_sent, webhook_sent, rate_limit_ip, rate_limit_applied, created_at
                    FROM audit_log
                    WHERE actor = 'Module3'
                    ORDER BY created_at DESC
                    LIMIT %s
                    """,
                    (limit,),
                )
                rows = cur.fetchall()
            self.conn.commit()

            actions = []
            for row in rows:
                actions.append({
                    'log_id': row[0],
                    'actor': row[1],
                    'action_type': row[2],
                    'meter_id': row[3],
                    'payload': row[4],
                    'email_sent': row[5],
                    'webhook_sent': row[6],
                    'rate_limit_ip': row[7],
                    'rate_limit_applied': row[8],
                    'created_at': row[9].isoformat() if row[9] else None,
                })
            return actions

        except psycopg2.Error as e:
            print(f"[DatabaseLogger] ❌ Query error: {e}")
            self.conn.rollback()
            return []

    def get_actions_by_meter(self, meter_id: str, limit: int = 20) -> list:
        if not self.connected:
            print(f"[DatabaseLogger] ❌ Not connected to database")
            return []
        try:
            with self.conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT log_id, actor, action_type, target_entity, payload, email_sent, webhook_sent, rate_limit_ip, rate_limit_applied, created_at
                    FROM audit_log
                    WHERE target_entity = %s
                    ORDER BY created_at DESC
                    LIMIT %s
                    """,
                    (meter_id, limit),
                )
                rows = cur.fetchall()
            self.conn.commit()

            actions = []
            for row in rows:
                actions.append({
                    'log_id': row[0],
                    'actor': row[1],
                    'action_type': row[2],
                    'meter_id': row[3],
                    'payload': row[4],
                    'email_sent': row[5],
                    'webhook_sent': row[6],
                    'rate_limit_ip': row[7],
                    'rate_limit_applied': row[8],
                    'created_at': row[9].isoformat() if row[9] else None,
                })
            return actions

        except psycopg2.Error as e:
            print(f"[DatabaseLogger] ❌ Query error: {e}")
            self.conn.rollback()
            return []

    def get_action_counts(self) -> dict:
        if not self.connected:
            print(f"[DatabaseLogger] ❌ Not connected to database")
            return {}
        try:
            with self.conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT action_type, COUNT(*) as count
                    FROM audit_log
                    WHERE actor = 'Module3'
                    GROUP BY action_type
                    """
                )
                rows = cur.fetchall()
            self.conn.commit()

            counts = {}
            for row in rows:
                counts[row[0]] = row[1]
            return counts

        except psycopg2.Error as e:
            print(f"[DatabaseLogger] ❌ Query error: {e}")
            self.conn.rollback()
            return {}

    def insert_alert(self, decision, behavior_type: str = "UNKNOWN") -> bool:
        if not self.connected:
            return False
        if decision.tier.value < 2:
            return True
        try:
            with self.conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO alerts (meter_id, risk_score, response_tier, behavior_type)
                    VALUES (%s, %s, %s, %s)
                    RETURNING alert_id
                    """,
                    (decision.meter_id, decision.risk_score, decision.tier.value, behavior_type),
                )
                alert_id = cur.fetchone()[0]
            self.conn.commit()
            print(f"[DatabaseLogger] ✅ Alert {alert_id} created for {decision.meter_id} (tier {decision.tier.value})")
            return True
        except psycopg2.Error as e:
            print(f"[DatabaseLogger] ❌ Alert insert error: {e}")
            self.conn.rollback()
            return False

    def set_meter_state(self, meter_id: str, state: str, ip_address: str = None) -> bool:
        """
        Updates the meters table's state column. This is what Module 4's
        dashboard actually reads to find quarantined meters.

        Uses an UPSERT (INSERT ... ON CONFLICT DO UPDATE) rather than a
        plain UPDATE, because not every tier registers the meter first
        (only Tier 3's rate limiter does, via meter_ip_registry.py). A
        plain UPDATE against a meter_id that doesn't exist yet silently
        affects 0 rows without erroring -- this ensures the row exists
        either way.
        """
        if not self.connected:
            return False
        try:
            with self.conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO meters (meter_id, ip_address, state, last_updated)
                    VALUES (%s, %s, %s, NOW())
                    ON CONFLICT (meter_id) DO UPDATE
                    SET state = EXCLUDED.state, last_updated = NOW()
                    """,
                    (meter_id, ip_address, state),
                )
            self.conn.commit()
            print(f"[DatabaseLogger] ✅ Set {meter_id} state to {state}")
            return True
        except psycopg2.Error as e:
            print(f"[DatabaseLogger] ❌ set_meter_state error: {e}")
            self.conn.rollback()
            return False

    def close(self):
        if self.conn:
            self.conn.close()
            self.connected = False
            print(f"[DatabaseLogger] Connection closed")


if __name__ == "__main__":
    from module3_step1_response_engine import GraduatedResponseEngine

    print("=" * 60)
    print("Module 3: Graduated Response Engine - STEP 4")
    print("Database Logger (with delivery + rate-limit tracking)")
    print("=" * 60)
    print()

    logger = DatabaseLogger()
    if not logger.connect():
        print("❌ Could not connect to database. Make sure PostgreSQL is running.")
        sys.exit(1)

    engine = GraduatedResponseEngine()
    test_cases = [
        ("meter_001", 25.0),
        ("meter_002", 65.0),
        ("meter_003", 85.0),
        ("meter_004", 98.0),
    ]

    print("[TEST] Logging decisions...\n")

    for meter_id, risk_score in test_cases:
        decision = engine.decide_response(meter_id, risk_score)
        if decision.tier.value == 2:
            logger.log_decision(decision, email_sent=True, webhook_sent=True)
        elif decision.tier.value == 3:
            logger.log_decision(decision, rate_limit_ip="10.99.9.9", rate_limit_applied=True)
        else:
            logger.log_decision(decision)

    print()
    print("[TEST] Retrieving recent actions...\n")

    recent = logger.get_recent_actions(limit=10)
    for action in recent:
        print(f"  {action['meter_id']:20} | {action['action_type']:16} | "
              f"email={action['email_sent']} | webhook={action['webhook_sent']} | "
              f"rl_ip={action['rate_limit_ip']} | rl_applied={action['rate_limit_applied']}")

    logger.close()

    print()
    print("=" * 60)
    print("✅ Step 4 Complete!")
    print("=" * 60)
