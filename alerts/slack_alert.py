"""
Slack alert channel via Incoming Webhooks.

Set in your .env:
  SLACK_WEBHOOK_URL = https://hooks.slack.com/services/T.../B.../...
"""
import os
import json
import urllib.request
import urllib.error

from shared.utils import get_logger

logger = get_logger(__name__)


def send_slack_alert(message: str, level: str = "CRITICAL") -> bool:
    """
    Post a message to the configured Slack channel.
    Returns True on success, False on failure.
    Silently skips if SLACK_WEBHOOK_URL is not set.
    """
    webhook_url = os.getenv("SLACK_WEBHOOK_URL", "")
    if not webhook_url:
        logger.debug("Slack alert skipped — SLACK_WEBHOOK_URL not set.")
        return False

    # Choose emoji based on severity
    emoji = {"CRITICAL": ":rotating_light:", "WARNING": ":warning:", "INFO": ":information_source:"}.get(
        level, ":bell:"
    )

    payload = {
        "text": f"{emoji} *[SmartGrid {level}]* {message}",
        "username": "SmartGrid AI",
        "icon_emoji": ":zap:",
    }

    try:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            webhook_url,
            data=data,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            if resp.status == 200:
                logger.info(f"Slack alert sent: {message[:60]}")
                return True
            else:
                logger.warning(f"Slack returned status {resp.status}")
                return False
    except urllib.error.URLError as e:
        logger.error(f"Failed to send Slack alert: {e}")
        return False
