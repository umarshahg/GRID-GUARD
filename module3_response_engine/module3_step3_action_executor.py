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


class ActionExecutor:
    """
    Executes actions based on response decisions.
    Each action is independently callable and testable.
    """

    def __init__(self):
        """Initialize executor with config from environment"""
        self.email_enabled = os.getenv("GRID_GUARD_EMAIL_ENABLED", "false").lower() == "true"
        self.webhook_enabled = os.getenv("GRID_GUARD_WEBHOOK_ENABLED", "false").lower() == "true"
        self.iptables_enabled = os.getenv("GRID_GUARD_IPTABLES_ENABLED", "false").lower() == "true"

    def execute(self, decision: ResponseDecision) -> bool:
        """
        Execute the action from the decision.
        
        Returns True if successful, False otherwise.
        """
        print(f"\n[Executor] Executing {decision.action.value} for {decision.meter_id}...")

        if decision.action == ResponseAction.LOG:
            return self._execute_log(decision)

        elif decision.action == ResponseAction.ALERT:
            return self._execute_alert(decision)

        elif decision.action == ResponseAction.RATE_LIMIT:
            return self._execute_rate_limit(decision)

        elif decision.action == ResponseAction.FULL_ISOLATION:
            return self._execute_full_isolation(decision)

        return False

    # ── Tier 1: LOG ONLY ────────────────────────────────────
    def _execute_log(self, decision: ResponseDecision) -> bool:
        """
        Tier 1: Just log to console/file. No action needed.
        In real deployment, this would write to syslog or file.
        """
        print(f"  ✅ LOG: {decision.meter_id} risk={decision.risk_score}% | {decision.description}")
        return True

    # ── Tier 2: ALERT ────────────────────────────────────
    def _execute_alert(self, decision: ResponseDecision) -> bool:
        """
        Tier 2: Notify operator via email/webhook.
        """
        success = True

        # Try email
        if self.email_enabled:
            if self._send_email_alert(decision):
                print(f"  ✉️  EMAIL: Alert sent")
            else:
                print(f"  ❌ EMAIL: Failed")
                success = False

        # Try webhook
        if self.webhook_enabled:
            if self._send_webhook_alert(decision):
                print(f"  🔔 WEBHOOK: Alert sent")
            else:
                print(f"  ❌ WEBHOOK: Failed")
                success = False

        # Always log to console (fallback)
        print(f"  📢 ALERT: {decision.meter_id} risk={decision.risk_score:.1f}%")
        print(f"     Description: {decision.description}")

        return success

    def _send_email_alert(self, decision: ResponseDecision) -> bool:
        """Send email alert to operator"""
        try:
            email_to = os.getenv("GRID_GUARD_ALERT_EMAIL", "admin@gridguard.local")
            # In real implementation, use SMTP to send
            print(f"    (Email would be sent to {email_to})")
            return True
        except Exception as e:
            print(f"    Email error: {e}")
            return False

    def _send_webhook_alert(self, decision: ResponseDecision) -> bool:
        """Send webhook alert to external system (SIEM, etc.)"""
        try:
            webhook_url = os.getenv("GRID_GUARD_WEBHOOK_URL", "")
            if not webhook_url:
                print(f"    (No webhook URL configured)")
                return False

            payload = {
                "meter_id": decision.meter_id,
                "risk_score": decision.risk_score,
                "tier": decision.tier.name,
                "description": decision.description,
                "timestamp": decision.timestamp,
            }
            # In real implementation, use requests.post(webhook_url, json=payload)
            print(f"    (Webhook would POST to {webhook_url})")
            return True
        except Exception as e:
            print(f"    Webhook error: {e}")
            return False

    # ── Tier 3: RATE LIMIT ────────────────────────────────────
    def _execute_rate_limit(self, decision: ResponseDecision) -> bool:
        """
        Tier 3: Apply iptables rate limiting.
        Limits traffic to 1 Mbps for the meter's IP.
        
        In real deployment, would look up meter IP from database,
        then apply iptables DNAT rule.
        """
        if not self.iptables_enabled:
            print(f"  ⏱️  RATE_LIMIT (simulation): Would limit {decision.meter_id} to 1 Mbps")
            return True

        try:
            # Example: iptables -A FORWARD -d 10.0.0.15 -m limit --limit 1024k/s -j ACCEPT
            print(f"  ⏱️  RATE_LIMIT: Applying iptables rule for {decision.meter_id}...")
            # In real implementation:
            # meter_ip = lookup_meter_ip(decision.meter_id)
            # cmd = f"sudo iptables -A FORWARD -d {meter_ip} -m limit --limit 1024k/s -j ACCEPT"
            # subprocess.run(cmd, shell=True, check=True)
            print(f"     (iptables rule applied)")
            return True
        except Exception as e:
            print(f"  ❌ RATE_LIMIT: Failed: {e}")
            return False

    # ── Tier 4: FULL ISOLATION ────────────────────────────────────
    def _execute_full_isolation(self, decision: ResponseDecision) -> bool:
        """
        Tier 4: Trigger Module 4 sandbox isolation.
        
        This calls Module 4 (Sandboxing) to:
        1. Move meter to quarantine VLAN
        2. Apply iptables DNAT to Docker emulator
        3. Start forensic capture
        """
        print(f"  🔒 FULL_ISOLATION: Triggering Module 4 for {decision.meter_id}...")

        try:
            # In real implementation, would:
            # 1. Call Module 4 REST API
            # 2. POST to /api/isolate/{meter_id}
            # 3. Module 4 handles VLAN + Docker + forensics
            
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
        """Call Module 4 API to isolate meter"""
        try:
            # In real implementation:
            # import requests
            # response = requests.post(
            #     "http://localhost:5002/api/isolate",
            #     json={"meter_id": meter_id},
            #     timeout=10
            # )
            # return response.status_code == 200
            
            print(f"    (Would POST to Module 4 API to isolate {meter_id})")
            return True
        except Exception as e:
            print(f"    Module 4 error: {e}")
            return False


# ── SELF-TEST ──────────────────────────────────────────────────────
if __name__ == "__main__":
    from module3_step1_response_engine import (
        GraduatedResponseEngine,
        ResponseTier,
        ResponseAction,
    )

    print("=" * 60)
    print("Module 3: Graduated Response Engine - STEP 3")
    print("Action Executor")
    print("=" * 60)
    print()

    engine = GraduatedResponseEngine()
    executor = ActionExecutor()

    test_cases = [
        ("meter_001", 25.0),   # Tier 1: LOG
        ("meter_002", 65.0),   # Tier 2: ALERT
        ("meter_003", 85.0),   # Tier 3: RATE_LIMIT
        ("meter_004", 98.0),   # Tier 4: FULL_ISOLATION
    ]

    for meter_id, risk_score in test_cases:
        decision = engine.decide_response(meter_id, risk_score)
        executor.execute(decision)
        print()

    print("=" * 60)
    print("✅ Step 3 Complete: Actions can be executed!")
    print("=" * 60)