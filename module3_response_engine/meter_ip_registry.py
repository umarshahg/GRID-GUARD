"""
GRID GUARD — Module 3: Meter IP Registry

Real iptables rules need a real IP address to target. Nothing in the
system currently populates one -- the `meters` table has an
ip_address column (per SDS 3.5.2) but nothing writes to it.

This module closes that gap: the first time a meter_id is seen, it's
assigned a deterministic IP (based on a hash of its name, so the same
meter always gets the same IP across runs) in the 10.99.0.0/16 range
-- reserved for private networks, guaranteed not to collide with
anything real on your machine or network.

The IP is stored in the `meters` table so it can be looked up again
for future rate-limit actions on the same meter.
"""

import hashlib
import os

import psycopg2


def _get_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5432"),
        database=os.getenv("DB_NAME", "gridguard"),
        user=os.getenv("DB_USER", "gridguard"),
        password=os.getenv("DB_PASSWORD", "gridguard"),
    )


def _deterministic_ip(meter_id: str) -> str:
    """Same meter_id always produces the same IP, across restarts."""
    digest = hashlib.md5(meter_id.encode()).hexdigest()
    octet3 = int(digest[0:2], 16)
    octet4 = int(digest[2:4], 16)
    return f"10.99.{octet3}.{octet4}"


def get_or_assign_meter_ip(meter_id: str) -> str:
    """
    Returns the meter's IP, registering it in the `meters` table if
    this is the first time we've seen it.
    """
    ip = _deterministic_ip(meter_id)

    conn = _get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO meters (meter_id, ip_address)
                VALUES (%s, %s)
                ON CONFLICT (meter_id) DO NOTHING
                """,
                (meter_id, ip),
            )
            conn.commit()
            cur.execute("SELECT ip_address FROM meters WHERE meter_id = %s", (meter_id,))
            row = cur.fetchone()
            return str(row[0]) if row else ip
    finally:
        conn.close()
