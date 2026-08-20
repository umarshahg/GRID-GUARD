"""
GRID GUARD — Module 3: Graduated Response Engine
STEP 1: Core Decision Logic

Per SRS Module 3 (FE-1 through FE-4):
  Tier 1 (Risk < 60%)         -> LOG ONLY
  Tier 2 (Risk 60-80%)        -> ALERT
  Tier 3 (Risk 80-95%)        -> RATE_LIMIT
  Tier 4 (Risk >= 95%)        -> FULL_ISOLATION

This step only decides WHAT to do — it does not talk to Redis,
Postgres, or iptables yet. That keeps it independently testable
before wiring it into anything live (Step 2 onward).
"""

from enum import Enum
from dataclasses import dataclass
from datetime import datetime, timezone


class ResponseTier(Enum):
    NORMAL = 1
    ALERT = 2
    RATE_LIMIT = 3
    FULL_ISOLATION = 4


class ResponseAction(Enum):
    LOG = "LOG"
    ALERT = "ALERT"
    RATE_LIMIT = "RATE_LIMIT"
    FULL_ISOLATION = "FULL_ISOLATION"


@dataclass
class ResponseDecision:
    meter_id: str
    risk_score: float
    tier: ResponseTier
    action: ResponseAction
    description: str
    timestamp: str


class GraduatedResponseEngine:
    """
    Maps a calibrated ensemble risk score (0-100, from Module 2)
    to a graduated response tier and action, per SRS Module 3.
    """

    # Thresholds match SRS FE-1..FE-4 exactly.
    ALERT_THRESHOLD = 60.0
    RATE_LIMIT_THRESHOLD = 80.0
    ISOLATION_THRESHOLD = 95.0

    def decide_response(self, meter_id: str, risk_score: float) -> ResponseDecision:
        """
        Evaluate a risk score and return the decision.
        Does not execute anything — just decides.
        """
        if risk_score < self.ALERT_THRESHOLD:
            tier = ResponseTier.NORMAL
            action = ResponseAction.LOG
            description = "Normal operation - risk is low"

        elif risk_score < self.RATE_LIMIT_THRESHOLD:
            tier = ResponseTier.ALERT
            action = ResponseAction.ALERT
            description = "Medium risk detected - operator notification sent"

        elif risk_score < self.ISOLATION_THRESHOLD:
            tier = ResponseTier.RATE_LIMIT
            action = ResponseAction.RATE_LIMIT
            description = "High risk detected - traffic rate-limited, suspicious commands blocked"

        else:
            tier = ResponseTier.FULL_ISOLATION
            action = ResponseAction.FULL_ISOLATION
            description = "Critical risk - meter isolated to quarantine VLAN, sandbox triggered"

        return ResponseDecision(
            meter_id=meter_id,
            risk_score=risk_score,
            tier=tier,
            action=action,
            description=description,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )


# ── Self-test when run directly ────────────────────────────────
if __name__ == "__main__":
    print("=" * 60)
    print("Module 3: Graduated Response Engine - STEP 1")
    print("=" * 60)
    print()
    print("[TEST] Decision Engine:")
    print()

    engine = GraduatedResponseEngine()

    test_cases = [
        ("meter_001", 25.0),
        ("meter_002", 65.0),
        ("meter_003", 85.0),
        ("meter_004", 98.0),
    ]

    for meter_id, risk_score in test_cases:
        decision = engine.decide_response(meter_id, risk_score)
        print(f"Input:  {decision.meter_id} | Risk: {decision.risk_score:.1f}%")
        print(f"Output: Tier {decision.tier.value} ({decision.tier.name})")
        print(f"Action: {decision.action.value}")
        print(f"Reason: {decision.description}")
        print("-" * 60)

    print()
    print("✅ Step 1 Complete: Response decision logic works!")
