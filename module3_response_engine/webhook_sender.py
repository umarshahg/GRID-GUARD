"""
Real webhook-sending implementation for Module 3 alerts.
POSTs a JSON payload to a configured HTTPS endpoint -- e.g. Slack,
a SIEM, or any custom receiver.

Required env var:
    GRID_GUARD_WEBHOOK_URL   the endpoint to POST alerts to
"""
import os
import requests


def send_webhook_alert(decision) -> bool:
    webhook_url = os.getenv("GRID_GUARD_WEBHOOK_URL", "")
    if not webhook_url:
        print("    (Webhook not sent -- GRID_GUARD_WEBHOOK_URL not configured)")
        return False

    payload = {
        "meter_id": decision.meter_id,
        "risk_score": decision.risk_score,
        "tier": decision.tier.value,
        "action": decision.action.value,
        "description": decision.description,
        "timestamp": decision.timestamp,
    }

    try:
        response = requests.post(webhook_url, json=payload, timeout=10)
        response.raise_for_status()
        print(f"    Webhook POSTed to {webhook_url} (status {response.status_code})")
        return True
    except requests.RequestException as e:
        print(f"    Webhook error: {e}")
        return False
