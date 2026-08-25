"""
GRID GUARD — Module 4: Sandboxing and Isolation
FE-2: Traffic Redirection (iptables DNAT)

Per SDS Section 3.2: redirect traffic from a quarantined meter's IP
to a Docker container running on a quarantine network. Uses iptables
DNAT to intercept outbound traffic and force it through forensic capture.

Real implementation — actual iptables rules applied to the kernel.
"""

import subprocess
import logging
from typing import Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TrafficRedirection")

QUARANTINE_CONTAINER_IP = "172.20.0.10"  # Per Module 4 design: meter emulator container
QUARANTINE_CONTAINER_PORT = 4059  # DLMS/COSEM standard port

def create_dnat_rule(meter_id: str, meter_ip: str, container_ip: str = QUARANTINE_CONTAINER_IP,
                     container_port: int = QUARANTINE_CONTAINER_PORT) -> dict:
    """
    Create an iptables DNAT rule: redirect traffic from meter_ip to container_ip:container_port.
    
    Rule structure:
    iptables -t nat -A OUTPUT -d <meter_ip> -p tcp --dport 4059 -j DNAT --to-destination <container_ip>:<container_port>
    
    This forces the meter's outbound traffic (if it tries to communicate) to the quarantine container.
    """
    rule_name = f"quarantine-{meter_id}"
    cmd = [
        "sudo", "iptables", "-t", "nat", "-A", "OUTPUT",
        "-d", meter_ip,
        "-p", "tcp",
        "--dport", str(container_port),
        "-j", "DNAT",
        "--to-destination", f"{container_ip}:{container_port}",
        "-m", "comment",
        "--comment", rule_name
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        logger.info(f"[FE-2] DNAT rule created: {meter_id} ({meter_ip}) → {container_ip}:{container_port}")
        return {
            "meter_id": meter_id,
            "meter_ip": meter_ip,
            "container_ip": container_ip,
            "container_port": container_port,
            "rule_name": rule_name,
            "applied": True,
            "simulated": False,
        }
    except subprocess.CalledProcessError as e:
        logger.error(f"[FE-2] Failed to create DNAT rule: {e.stderr}")
        return {
            "meter_id": meter_id,
            "applied": False,
            "simulated": False,
            "error": str(e),
        }

def delete_dnat_rule(meter_id: str, meter_ip: str, container_ip: str = QUARANTINE_CONTAINER_IP,
                     container_port: int = QUARANTINE_CONTAINER_PORT) -> dict:
    """
    Delete a DNAT rule for a meter (called during FE-5 release).
    """
    rule_name = f"quarantine-{meter_id}"
    cmd = [
        "sudo", "iptables", "-t", "nat", "-D", "OUTPUT",
        "-d", meter_ip,
        "-p", "tcp",
        "--dport", str(container_port),
        "-j", "DNAT",
        "--to-destination", f"{container_ip}:{container_port}",
        "-m", "comment",
        "--comment", rule_name
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        logger.info(f"[FE-2] DNAT rule deleted: {meter_id}")
        return {
            "meter_id": meter_id,
            "deleted": True,
            "simulated": False,
        }
    except subprocess.CalledProcessError as e:
        logger.error(f"[FE-2] Failed to delete DNAT rule: {e.stderr}")
        return {
            "meter_id": meter_id,
            "deleted": False,
            "simulated": False,
            "error": str(e),
        }

def list_dnat_rules() -> list:
    """
    List all active DNAT rules for quarantined meters.
    """
    cmd = ["sudo", "iptables", "-t", "nat", "-L", "OUTPUT", "-n", "-v"]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        logger.info(f"[FE-2] Current DNAT rules:\n{result.stdout}")
        return result.stdout.split("\n")
    except subprocess.CalledProcessError as e:
        logger.error(f"[FE-2] Failed to list DNAT rules: {e.stderr}")
        return []

if __name__ == "__main__":
    print("=" * 60)
    print("Module 4: FE-2 Traffic Redirection (iptables DNAT) - self-test")
    print("=" * 60)
    print("\nNote: This test requires sudo privileges to actually apply iptables rules.")
    print("If you see 'applied: False' below, sudo may not be available in this context.\n")
    
    # Test with a mock meter
    test_meter_id = "SM-FE2-TEST"
    test_meter_ip = "192.168.1.100"
    
    print(f"Creating DNAT rule for {test_meter_id} ({test_meter_ip})...")
    result = create_dnat_rule(test_meter_id, test_meter_ip)
    print(f"Result: {result}\n")
    
    print("Listing active DNAT rules...")
    rules = list_dnat_rules()
    
    if result.get("applied"):
        print(f"\nDeleting DNAT rule for {test_meter_id}...")
        delete_result = delete_dnat_rule(test_meter_id, test_meter_ip)
        print(f"Delete result: {delete_result}")
