"""Sends one SMS in the background, so the USSD screen never waits for it.

It sends only when AT_API_KEY is set (Render: Environment tab). AT_USERNAME is "sandbox" for testing
(messages show in the Africa's Talking simulator) or the live app's username for real SMS.
"""
import logging
import os
import threading

log = logging.getLogger("sokoradar.sms")


def enabled():
    return bool(os.environ.get("AT_API_KEY"))


def _send(phone, message):
    try:
        import africastalking
        africastalking.initialize(os.environ.get("AT_USERNAME", "sandbox"), os.environ["AT_API_KEY"])
        sender = os.environ.get("AT_SENDER_ID")
        r = africastalking.SMS.send(message, [phone], sender) if sender else africastalking.SMS.send(message, [phone])
        rec = (r.get("SMSMessageData", {}).get("Recipients") or [{}])[0]
        log.warning("SMS to %s: %s", phone, rec.get("status", r))
    except Exception:                                   # never break the USSD session over an SMS
        log.exception("SMS to %s failed", phone)


def send_later(phone, message):
    """Start sending and return at once. Returns False when SMS sending is not set up."""
    if not (enabled() and phone and message):
        return False
    threading.Thread(target=_send, args=(phone, message), daemon=True).start()
    return True
