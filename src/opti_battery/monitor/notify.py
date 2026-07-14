"""
Notifications for the auto-discovery monitor.

Always prints to the console. If NOTIFY_WEBHOOK is set in the environment,
also POSTs a JSON payload {"text": message} to that URL — which works
out-of-the-box for Slack and Discord incoming webhooks, and most
generic webhook receivers.

Uses only the standard library (urllib) so no extra dependency is needed.
"""
import os
import json
import urllib.request


def notify(message: str) -> None:
    print(message)

    webhook = os.getenv("NOTIFY_WEBHOOK")
    if not webhook:
        return

    try:
        payload = json.dumps({"text": message}).encode("utf-8")
        req = urllib.request.Request(
            webhook, data=payload,
            headers={"Content-Type": "application/json"},
        )
        urllib.request.urlopen(req, timeout=10)
    except Exception as e:
        print(f"  (notify webhook failed: {e})")
