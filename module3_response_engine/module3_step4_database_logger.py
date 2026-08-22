"""
GRID GUARD — Module 3: Graduated Response Engine
STEP 4: Database Logger

Takes ResponseDecision from Step 3 and SAVES it to PostgreSQL
audit_log table so the Dashboard can display what actions were taken.

This bridges the gap between:
  - Step 3 (Execute action in real-time)
  - Step 5 (Dashboard queries and displays)

Stores to audit_log table with fields:
  - log_id (auto-increment)
  - meter_id
  - action_type (LOG, ALERT, RATE_LIMIT, FULL_ISOLATION)
  - risk_score
  - description
  - created_at (timestamp)

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
    """
    Logs ResponseDecisions to PostgreSQL audit_log table.
    
    This makes actions persistent and queryable by the Dashboard.
    """

    def __init__(self):
        """Initialize database connection from environment"""
        self.db_host = os.getenv("DB_HOST", "localhost")
        self.db_port = os.getenv("DB_PORT", "5432")
        self.db_name = os.getenv("DB_NAME", "gridguard")
        self.db_user = os.getenv("DB_USER", "gridguard")
        self.db_password = os.getenv("DB_PASSWORD", "gridguard")
        
        self.conn = None
        self.connected = False

    def connect(self) -> bool:
        """
        Connect to PostgreSQL database.
        
        Returns True if successful, False otherwise.
        """
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

    def log_decision(self, decision: ResponseDecision) -> bool:
        """
        Log a ResponseDecision to audit_log table.
        
        Args:
            decision: ResponseDecision object from Step 3
        
        Returns:
            True if successful, False otherwise
        """
        if not self.connected:
            print(f"[DatabaseLogger] ❌ Not connected to database")
            return False

        try:
            with self.conn.cursor() as cur:
                # Insert into audit_log
                cur.execute(
                    """
                    INSERT INTO audit_log 
                    (actor, action_type, target_entity, payload, created_at)
                    VALUES (%s, %s, %s, %s, NOW())
                    """,
                    (
                        "Module3",  # actor (who took action)
                        decision.action.value,  # action_type (LOG, ALERT, RATE_LIMIT, FULL_ISOLATION)
                        decision.meter_id,  # target_entity (which meter)
                        str(decision.to_dict()),  # payload (full decision data)
                    ),
                )
            self.conn.commit()
            print(f"[DatabaseLogger] ✅ Logged {decision.action.value} for {decision.meter_id} (risk={decision.risk_score}%)")
            return True

        except psycopg2.Error as e:
            print(f"[DatabaseLogger] ❌ Database error: {e}")
            self.conn.rollback()
            return False
        except Exception as e:
            print(f"[DatabaseLogger] ❌ Error: {e}")
            return False

    def log_batch(self, decisions: list) -> int:
        """
        Log multiple ResponseDecisions at once.
        
        Args:
            decisions: List of ResponseDecision objects
        
        Returns:
            Number of records successfully logged
        """
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
        """
        Retrieve recent actions from audit_log.
        
        This is what the Dashboard will query.
        
        Args:
            limit: Number of recent actions to return
        
        Returns:
            List of dictionaries with action data
        """
        if not self.connected:
            print(f"[DatabaseLogger] ❌ Not connected to database")
            return []

        try:
            with self.conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT log_id, actor, action_type, target_entity, payload, created_at
                    FROM audit_log
                    WHERE actor = 'Module3'
                    ORDER BY created_at DESC
                    LIMIT %s
                    """,
                    (limit,),
                )
                
                rows = cur.fetchall()
                actions = []
                for row in rows:
                    actions.append({
                        'log_id': row[0],
                        'actor': row[1],
                        'action_type': row[2],
                        'meter_id': row[3],
                        'payload': row[4],
                        'created_at': row[5].isoformat() if row[5] else None,
                    })
                
                return actions

        except psycopg2.Error as e:
            print(f"[DatabaseLogger] ❌ Query error: {e}")
            return []

    def get_actions_by_meter(self, meter_id: str, limit: int = 20) -> list:
        """
        Get all actions for a specific meter.
        
        Useful for meter detail view in dashboard.
        
        Args:
            meter_id: The meter to query
            limit: Max records to return
        
        Returns:
            List of actions for that meter
        """
        if not self.connected:
            print(f"[DatabaseLogger] ❌ Not connected to database")
            return []

        try:
            with self.conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT log_id, actor, action_type, target_entity, payload, created_at
                    FROM audit_log
                    WHERE target_entity = %s
                    ORDER BY created_at DESC
                    LIMIT %s
                    """,
                    (meter_id, limit),
                )
                
                rows = cur.fetchall()
                actions = []
                for row in rows:
                    actions.append({
                        'log_id': row[0],
                        'actor': row[1],
                        'action_type': row[2],
                        'meter_id': row[3],
                        'payload': row[4],
                        'created_at': row[5].isoformat() if row[5] else None,
                    })
                
                return actions

        except psycopg2.Error as e:
            print(f"[DatabaseLogger] ❌ Query error: {e}")
            return []

    def get_action_counts(self) -> dict:
        """
        Get count of each action type.
        
        Useful for dashboard summary card.
        
        Returns:
            Dictionary with action counts
            Example: {
                'LOG': 1000,
                'ALERT': 50,
                'RATE_LIMIT': 10,
                'FULL_ISOLATION': 2
            }
        """
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
                counts = {}
                for row in rows:
                    counts[row[0]] = row[1]
                
                return counts

        except psycopg2.Error as e:
            print(f"[DatabaseLogger] ❌ Query error: {e}")
            return {}


    def insert_alert(self, decision, behavior_type: str = "UNKNOWN") -> bool:
        """
        Inserts into the dedicated `alerts` table for Tier 2+ decisions.
        Tier 1 (LOG) deliberately gets no alert row.
        """
        if not self.connected:
            return False
        if decision.tier.value < 2:
            return True  # Tier 1 is log-only, not an error

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

    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            self.connected = False
            print(f"[DatabaseLogger] Connection closed")


# ── SELF-TEST ──────────────────────────────────────────────────────
if __name__ == "__main__":
    from module3_step1_response_engine import (
        GraduatedResponseEngine,
        ResponseTier,
        ResponseAction,
    )

    print("=" * 60)
    print("Module 3: Graduated Response Engine - STEP 4")
    print("Database Logger")
    print("=" * 60)
    print()

    # Initialize logger
    logger = DatabaseLogger()
    
    # Connect to database
    if not logger.connect():
        print("❌ Could not connect to database. Make sure PostgreSQL is running.")
        sys.exit(1)

    # Generate test decisions
    engine = GraduatedResponseEngine()
    test_cases = [
        ("meter_001", 25.0),   # Tier 1: LOG
        ("meter_002", 65.0),   # Tier 2: ALERT
        ("meter_003", 85.0),   # Tier 3: RATE_LIMIT
        ("meter_004", 98.0),   # Tier 4: FULL_ISOLATION
    ]

    print("[TEST] Logging decisions to database...\n")

    decisions = []
    for meter_id, risk_score in test_cases:
        decision = engine.decide_response(meter_id, risk_score)
        decisions.append(decision)
        logger.log_decision(decision)

    print()
    print("[TEST] Retrieving recent actions from database...\n")

    recent = logger.get_recent_actions(limit=10)
    for action in recent:
        print(f"  {action['created_at']} | {action['action_type']:20} | {action['meter_id']}")

    print()
    print("[TEST] Action counts by type:\n")

    counts = logger.get_action_counts()
    for action_type, count in counts.items():
        print(f"  {action_type:20} | {count} actions")

    print()
    print("[TEST] Actions for meter_002:\n")

    meter_actions = logger.get_actions_by_meter("meter_002")
    for action in meter_actions:
        print(f"  {action['created_at']} | {action['action_type']} | {action['payload']}")

    # Close connection
    logger.close()

    print()
    print("=" * 60)
    print("✅ Step 4 Complete: Actions logged to database!")
    print("=" * 60)
    print()
    print("Next: Step 5 will expose this data via REST API for Dashboard")
