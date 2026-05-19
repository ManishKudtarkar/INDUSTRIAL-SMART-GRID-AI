"""
Email alert channel.

Reads SMTP credentials from environment variables (never hardcoded).
Set these in your .env file:
  ALERT_EMAIL_FROM     = sender@example.com
  ALERT_EMAIL_TO       = ops-team@example.com
  ALERT_EMAIL_PASSWORD = <app-password>
  ALERT_SMTP_HOST      = smtp.gmail.com
  ALERT_SMTP_PORT      = 587
"""
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from shared.utils import get_logger

logger = get_logger(__name__)


def send_email_alert(subject: str, body: str) -> bool:
    """
    Send an email alert.  Returns True on success, False on failure.
    Silently skips if credentials are not configured.
    """
    smtp_host = os.getenv("ALERT_SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(os.getenv("ALERT_SMTP_PORT", "587"))
    from_addr = os.getenv("ALERT_EMAIL_FROM", "")
    to_addr   = os.getenv("ALERT_EMAIL_TO", "")
    password  = os.getenv("ALERT_EMAIL_PASSWORD", "")

    if not all([from_addr, to_addr, password]):
        logger.debug("Email alert skipped — ALERT_EMAIL_* env vars not set.")
        return False

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"[SmartGrid Alert] {subject}"
        msg["From"]    = from_addr
        msg["To"]      = to_addr
        msg.attach(MIMEText(body, "plain"))

        with smtplib.SMTP(smtp_host, smtp_port, timeout=10) as server:
            server.ehlo()
            server.starttls()
            server.login(from_addr, password)
            server.sendmail(from_addr, to_addr, msg.as_string())

        logger.info(f"Email alert sent to {to_addr}: {subject}")
        return True

    except Exception as e:
        logger.error(f"Failed to send email alert: {e}")
        return False
