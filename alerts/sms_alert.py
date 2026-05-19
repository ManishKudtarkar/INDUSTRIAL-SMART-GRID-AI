"""
SMS alert channel via Twilio.

Set in your .env:
  TWILIO_ACCOUNT_SID = ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
  TWILIO_AUTH_TOKEN  = your_auth_token
  TWILIO_FROM_NUMBER = +1xxxxxxxxxx
  TWILIO_TO_NUMBER   = +1xxxxxxxxxx

Twilio is optional — if credentials are absent the function silently skips.
"""
import os
import urllib.request
import urllib.parse
import urllib.error
import base64

from shared.utils import get_logger

logger = get_logger(__name__)

TWILIO_API_URL = "https://api.twilio.com/2010-04-01/Accounts/{sid}/Messages.json"


def send_sms_alert(message: str) -> bool:
    """
    Send an SMS via Twilio REST API (no SDK required).
    Returns True on success, False on failure.
    """
    account_sid = os.getenv("TWILIO_ACCOUNT_SID", "")
    auth_token  = os.getenv("TWILIO_AUTH_TOKEN", "")
    from_number = os.getenv("TWILIO_FROM_NUMBER", "")
    to_number   = os.getenv("TWILIO_TO_NUMBER", "")

    if not all([account_sid, auth_token, from_number, to_number]):
        logger.debug("SMS alert skipped — TWILIO_* env vars not set.")
        return False

    url = TWILIO_API_URL.format(sid=account_sid)
    body = urllib.parse.urlencode({
        "From": from_number,
        "To":   to_number,
        "Body": f"[SmartGrid Alert] {message}",
    }).encode("utf-8")

    credentials = base64.b64encode(f"{account_sid}:{auth_token}".encode()).decode()
    req = urllib.request.Request(
        url,
        data=body,
        headers={
            "Authorization": f"Basic {credentials}",
            "Content-Type":  "application/x-www-form-urlencoded",
        },
    )

    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            if resp.status in (200, 201):
                logger.info(f"SMS alert sent to {to_number}")
                return True
            else:
                logger.warning(f"Twilio returned status {resp.status}")
                return False
    except urllib.error.URLError as e:
        logger.error(f"Failed to send SMS alert: {e}")
        return False
