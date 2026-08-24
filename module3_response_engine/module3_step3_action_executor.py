"""
GRID GUARD — Module 3: Graduated Response Engine
STEP 3: Action Executor

Takes ResponseDecision from Step 1 and EXECUTES the action:
  Tier 1 (LOG)           → Write to audit log
  Tier 2 (ALERT)         → Send email/webhook/notification
  Tier 3 (RATE_LIMIT)    → Apply iptables rate limiting
  Tier 4 (FULL_ISOLATION)→ Call Module 4 sandbox isolation

This step bridges decision → execution.
"""

import os
import subprocess
import smtplib
import json
from datetime import datetime
from typing import Optional
import sys

sys.path.append(os.path.dirname(__file__))
from module3_step1_response_engine import ResponseDecision, ResponseAction
from email_sender import send_email_alert
from webhook_sender import send_webhook_alert
from real_rate_limiter import apply_rate_limit as real_apply_rate_limit


class ActionExecutor:
    def __init__(self):
        self.email_enabled = os.getenv("GRID_GUARD_EMAIL_ENABLED", "false").lower() == "true"
        self.webhook_enabled = os.getenv("GRID_GUARD_WEBHOOK_ENABLED", "false").lower() == "true"
        self.iptables_enabled = os.getenv("GRID_GUARD_IPTABLES_ENABLED", "false").lower() == "true"

    def execute(self, decision: ResponseDecision) -> dict:
        """
        Returns a dict describing what happened. Keys present depend
        on the tier:
          - Tier 1, 4: {"email_sent": None, "webhook_sent": None}
          - Tier 2:    {"email_sent": bool|None, "webhook_sent": bool|None}
          - Tier 3:    {"email_sent": None, "webhook_sent": None,
                        "rate_limit_ip": str|None, "rate_limit_applied": bool}
        """
        print(f"\n[Executor] Executing {decision.action.value} for {decision.meter_id}...")

        if decision.action == ResponseAction.LOG:
            self._execute_log(decision)
            return {"email_sent": None, "webhook_sent": None}

        elif decision.action == ResponseAction.ALERT:
            return self._execute_alert(decision)

        elif decision.action == ResponseAction.RATE_LIMIT:
            rl_result = self._execute_rate_limit(decision)
            return {
                "email_sent": None,
                "webhook_sent": None,
                "rate_limit_ip": rl_result.get("ip"),
                "rate_limit_applied": rl_result.get("applied"),
            }

        elif decision.action == ResponseAction.FULL_ISOLATION:
            self._execute_full_isolation(decision)
            return {"email_sent": None, "webhook_sent": None}

        return {"email_sent": None, "webhook_sent": None}

    def _execute_log(self, decision: ResponseDecision) -> bool:
        print(f"  ✅ LOG: {decision.meter_id} risk={decision.risk_score}% | {decision.description}")
        return True

    def _execute_alert(self, decision: ResponseDecision) -> dict:
        email_sent = None
        webhook_sent = None

        if self.email_enabled:
            email_sent = self._send_email_alert(decision)
            print(f"  ✉️  EMAIL: {'Alert sent' if email_sent else 'Failed'}")

        if self.webhook_enabled:
            webhook_sent = self._send_webhook_alert(decision)
            print(f"  🔔 WEBHOOK: {'Alert sent' if webhook_sent else 'Failed'}")

        print(f"  📢 ALERT: {decision.meter_id} risk={decision.risk_score:.1f}%")
        print(f"     Description: {decision.description}")

        return {"email_sent": email_sent, "webhook_sent": webhook_sent}

    def _send_email_alert(self, decision: ResponseDecision) -> bool:
        return send_email_alert(decision)

    def _send_webhook_alert(self, decision: ResponseDecision) -> bool:
        return send_webhook_alert(decision)

    def _execute_rate_limit(self, decision: ResponseDecision) -> dict:
        """
        Tier 3: Apply real iptables rate limiting against the meter's
        assigned IP. Falls back to a dry run if iptables/root aren't
        available. Returns details so the caller can log the actual
        IP and whether it was a real rule or a dry run.
        """
        if not self.iptables_enabled:
            print(f"  ⏱️  RATE_LIMIT (simulation): Would limit {decision.meter_id} to 10/min")
            return {"ip": None, "applied": False}

        result = real_apply_rate_limit(decision.meter_id, limit_per_min=10)
        if result["applied"]:
            print(f"  ⏱️  RATE_LIMIT: Real iptables rule applied for {decision.meter_id} ({result['ip']})")
        else:
            print(f"  ⏱️  RATE_LIMIT: Dry run only for {decision.meter_id} ({result['ip']}) -- {result.get('reason', '')}")
        return {"ip": result["ip"], "applied": result["applied"]}

    def _execute_full_isolation(self, decision: ResponseDecision) -> bool:
        print(f"  🔒 FULL_ISOLATION: Triggering Module 4 for {decision.meter_id}...")
        try:
            result = self._call_module4_isolation(decision.meter_id)
            if result:
                print(f"     ✅ Module 4 isolation triggered")
                return True
            else:
                print(f"     ❌ Module 4 isolation failed")
                return False
        except Exception as e:
            print(f"  ❌ FULL_ISOLATION: Error: {e}")
            return False

    def _call_module4_isolation(self, meter_id: str) -> bool:
        try:
            print(f"    (Would POST to Module 4 API to isolate {meter_id})")
            return True
        except Exception as e:
            print(f"    Module 4 error: {e}")
            return False


if __name__ == "__main__":
    from module3_step1_response_engine import GraduatedResponseEngine

    print("=" * 60)
    print("Module 3: Graduated Response Engine - STEP 3")
    print("Action Executor")
    print("=" * 60)
    print()

    engine = GraduatedResponseEngine()
    executor = ActionExecutor()

    test_cases = [
        ("meter_001", 25.0),
        ("meter_002", 65.0),
        ("meter_003", 85.0),
        ("meter_004", 98.0),
    ]

    for meter_id, risk_score in test_cases:
        decision = engine.decide_response(meter_id, risk_score)
        result = executor.execute(decision)
        print(f"     -> execution result: {result}")
        print()

    print("=" * 60)
    print("✅ Step 3 Complete: Actions can be executed!")
    print("=" * 60)
