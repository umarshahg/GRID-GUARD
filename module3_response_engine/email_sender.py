"""
Real email-sending implementation for Module 3 alerts.
Uses smtplib with STARTTLS (when the server supports it), configured
entirely via environment variables so no credentials are hardcoded.

Required env vars:
    GRID_GUARD_SMTP_HOST       e.g. smtp.gmail.com
    GRID_GUARD_SMTP_PORT       e.g. 587
    GRID_GUARD_SMTP_USER       the sending account's email
    GRID_GUARD_SMTP_PASSWORD   an app password (NOT your normal password)
    GRID_GUARD_ALERT_EMAIL     who receives the alerts
"""
import os
import smtplib
from email.mime.text import MIMEText


def send_email_alert(decision) -> bool:
    smtp_host = os.getenv("GRID_GUARD_SMTP_HOST")
    smtp_port = int(os.getenv("GRID_GUARD_SMTP_PORT", "587"))
    smtp_user = os.getenv("GRID_GUARD_SMTP_USER")
    smtp_password = os.getenv("GRID_GUARD_SMTP_PASSWORD")
    to_email = os.getenv("GRID_GUARD_ALERT_EMAIL", "admin@gridguard.local")

    if not all([smtp_host, smtp_user, smtp_password]):
        print("    (Email not sent -- GRID_GUARD_SMTP_* env vars not fully configured)")
        return False

    subject = f"GRID GUARD Alert — {decision.meter_id} (Tier {decision.tier.value})"
    body = (
        f"Meter: {decision.meter_id}\n"
        f"Risk Score: {decision.risk_score:.1f}%\n"
        f"Tier: {decision.tier.value} ({decision.action.value})\n"
        f"Description: {decision.description}\n"
        f"Timestamp: {decision.timestamp}\n"
    )

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = smtp_user
    msg["To"] = to_email

    try:
        with smtplib.SMTP(smtp_host, smtp_port, timeout=10) as server:
            server.ehlo()
            if server.has_extn("STARTTLS"):
                server.starttls()
                server.ehlo()
            if smtp_password:
                try:
                    server.login(smtp_user, smtp_password)
                except smtplib.SMTPNotSupportedError:
                    pass
            server.sendmail(smtp_user, [to_email], msg.as_string())
        print(f"    Email sent to {to_email}")
        return True
    except Exception as e:
        print(f"    Email error: {e}")
        return False
