"""
GRID GUARD — Module 4: Sandboxing and Isolation
FE-1: VLAN Quarantine

Per SDS Section 3.1/3.4: a compromised meter's switch port should be
moved to a dedicated quarantine VLAN via a network switch's REST API.
This requires physical managed-switch hardware, which isn't available
in this environment. This module is an honest, clearly-labelled stub
-- it logs exactly what a real implementation would do and returns a
result the rest of the pipeline can act on, without pretending real
hardware was touched.

Real implementation would look like:
    response = requests.put(
        f"http://{switch_ip}/api/port/{switch_port}/vlan",
        json={"vlan_id": QUARANTINE_VLAN_ID},
        auth=(switch_user, switch_password),
    )
"""

QUARANTINE_VLAN_ID = 999  # per SDS: quarantine VLAN isolated from all production VLANs

def move_to_quarantine_vlan(meter_id: str, switch_port: str = None) -> dict:
    """
    STUB -- no real network switch available. Returns what a real
    call would have returned, clearly marked as simulated.
    """
    switch_port = switch_port or f"port-{meter_id}"
    print(f"    [VLANQuarantine] (STUB) Would move {meter_id} on {switch_port} "
          f"to VLAN {QUARANTINE_VLAN_ID} via switch REST API")
    return {
        "meter_id": meter_id,
        "switch_port": switch_port,
        "vlan_id": QUARANTINE_VLAN_ID,
        "applied": False,
        "simulated": True,
    }

def restore_original_vlan(meter_id: str, switch_port: str = None, original_vlan_id: int = 1) -> dict:
    """STUB -- restores the meter to its original VLAN on release (FE-5)."""
    switch_port = switch_port or f"port-{meter_id}"
    print(f"    [VLANQuarantine] (STUB) Would restore {meter_id} on {switch_port} "
          f"to VLAN {original_vlan_id}")
    return {
        "meter_id": meter_id,
        "switch_port": switch_port,
        "vlan_id": original_vlan_id,
        "applied": False,
        "simulated": True,
    }

if __name__ == "__main__":
    print("=" * 60)
    print("Module 4: FE-1 VLAN Quarantine (stub) - self-test")
    print("=" * 60)
    result = move_to_quarantine_vlan("SM-TEST-VLAN")
    print(f"Result: {result}")
    restore_result = restore_original_vlan("SM-TEST-VLAN")
    print(f"Restore result: {restore_result}")
