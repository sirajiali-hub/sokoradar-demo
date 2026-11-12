"""Send each SMS subscriber the spike alerts for their county (next month).

    python send_sms_alerts.py                 # dry run: prints the messages, sends nothing
    python send_sms_alerts.py --send          # sends through Africa's Talking
    python send_sms_alerts.py --to +254712345678 --county Garissa --lang so --send   # one test SMS to one phone

Settings come from environment variables (never put the API key in the code or in GitHub):
    AT_USERNAME   "sandbox" for testing (messages appear only in the simulator); your app username for real SMS
    AT_API_KEY    the API key of that app
    AT_SENDER_ID  optional, only if an approved sender ID exists
"""
import argparse
import os
import sys

import subscribers
from i18n import month, t
from sokoradar_data import county_alerts

SMS_MAX = 160


def message_for(county, lang="sw"):
    """The alert SMS for one county, in the subscriber's language (None when there is no alert)."""
    T = t(lang)
    rows = county_alerts(county, horizon=1)
    if not rows:
        return None
    parts = [f"{T['crops'][r['commodity']]} KES {r['forecast_price_kes']:.0f} "
             f"({r['range_low_kes']:.0f}-{r['range_high_kes']:.0f})" for r in rows]

    def build(items, more=""):
        return T["sms"].format(county=county, month=month(lang, rows[0]["target_month"]), items=", ".join(items) + more)

    msg = build(parts)
    while len(msg) > SMS_MAX and len(parts) > 1:          # keep it to one SMS
        parts.pop()
        msg = build(parts, T["sms_more"])
    return msg


def connect():
    """Africa's Talking SMS service, from environment variables. Live accounts send real SMS (and cost credit)."""
    import africastalking
    user, key = os.environ.get("AT_USERNAME", "sandbox"), os.environ.get("AT_API_KEY")
    if not key:
        sys.exit("Set AT_API_KEY first (and AT_USERNAME: 'sandbox' for testing, your app username for real SMS).")
    africastalking.initialize(user, key)
    print(f"Sending as Africa's Talking user '{user}'"
          + (" (sandbox: messages show in the simulator only)" if user == "sandbox" else " (LIVE: real SMS, uses credit)"))
    return africastalking.SMS


def send_one(sms, phone, msg):
    sender = os.environ.get("AT_SENDER_ID")
    try:
        r = sms.send(msg, [phone], sender) if sender else sms.send(msg, [phone])
    except Exception as e:                                  # wrong key, no credit, network ...
        print(f"    FAILED: {e}")
        return False
    rec = (r.get("SMSMessageData", {}).get("Recipients") or [{}])[0]
    print(f"    {rec.get('status', r)}  cost {rec.get('cost', '?')}")
    return rec.get("status") == "Success"


def main():
    ap = argparse.ArgumentParser(description="Send SokoRadar alert SMS")
    ap.add_argument("--send", action="store_true", help="really send (default: dry run, prints only)")
    ap.add_argument("--to", help="send ONE test SMS to this number (format +2547XXXXXXXX), instead of all subscribers")
    ap.add_argument("--county", default="Garissa", help="county for the --to test (default Garissa)")
    ap.add_argument("--lang", default="sw", help="language for the --to test: sw, en or so (default sw)")
    args = ap.parse_args()

    if args.to:                                             # one test message, e.g. to your own phone
        if not args.to.startswith("+") or not args.to[1:].isdigit():
            sys.exit("Use the international format, e.g. +254712345678")
        msg = message_for(args.county, args.lang) or t(args.lang)["no_alerts"].format(county=args.county)
        print(f"{args.to} [{args.county}, {args.lang}] ({len(msg)} chars): {msg}")
        if args.send:
            send_one(connect(), args.to, msg)
        else:
            print("Dry run: add --send to really send it.")
        return

    subs = subscribers.load()
    if not subs:
        sys.exit("No subscribers yet. Subscribe through the USSD menu (option 3) first, or test with --to.")
    sms = connect() if args.send else None
    sent = quiet = 0
    for s in subs:
        msg = message_for(s["county"], s.get("lang") or "sw")
        if msg is None:
            quiet += 1
            continue
        print(f"{s['phone']} [{s['county']}, {s.get('lang') or 'sw'}] ({len(msg)} chars): {msg}")
        if sms:
            send_one(sms, s["phone"], msg)
        sent += 1
    print(f"{'Sent' if sms else 'Would send'} {sent} SMS; {quiet} subscriber(s) had no alert this month.")


if __name__ == "__main__":
    main()
