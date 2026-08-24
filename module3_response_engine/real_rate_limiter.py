"""
GRID GUARD — Module 3: Real iptables Rate Limiter

Replaces the print-only Tier 3 simulation with an actual iptables
rule. Requires root privileges to run for real -- if the process
doesn't have them, this falls back to a clearly-labelled dry run
instead of crashing, so the rest of the pipeline still demonstrates
correctly even without root.
"""

import subprocess
import sys
import os

sys.path.append(os.path.dirname(__file__))
from meter_ip_registry import get_or_assign_meter_ip


def apply_rate_limit(meter_id: str, limit_per_min: int = 10) -> dict:
    """
    Looks up (or assigns) the meter's IP, then applies a real
    iptables rule limiting traffic to it.
    """
    ip = get_or_assign_meter_ip(meter_id)

    try:
        subprocess.run(
            ["iptables", "-A", "OUTPUT", "-d", ip,
             "-m", "limit", "--limit", f"{limit_per_min}/minute", "-j", "ACCEPT"],
            check=True, capture_output=True, text=True,
        )
        subprocess.run(
            ["iptables", "-A", "OUTPUT", "-d", ip, "-j", "DROP"],
            check=True, capture_output=True, text=True,
        )
        return {"applied": True, "ip": ip, "dry_run": False}

    except FileNotFoundError:
        print(f"    [RateLimiter] iptables not found on this system -- dry run only")
        return {"applied": False, "ip": ip, "dry_run": True, "reason": "iptables not installed"}

    except subprocess.CalledProcessError as e:
        print(f"    [RateLimiter] iptables failed (likely needs root): {e.stderr.strip() if e.stderr else e}")
        return {"applied": False, "ip": ip, "dry_run": True, "reason": str(e.stderr or e)}


def clear_rate_limit(meter_id: str) -> bool:
    """Removes previously applied rules for this meter."""
    ip = get_or_assign_meter_ip(meter_id)
    try:
        subprocess.run(["iptables", "-D", "OUTPUT", "-d", ip, "-j", "DROP"], check=False, capture_output=True)
        subprocess.run(
            ["iptables", "-D", "OUTPUT", "-d", ip, "-m", "limit", "--limit", "10/minute", "-j", "ACCEPT"],
            check=False, capture_output=True,
        )
        return True
    except Exception:
        return False
