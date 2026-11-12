"""Send each SMS subscriber the spike alerts for their county (next month).

    python send_sms_alerts.py                 # dry run: prints the messages, sends nothing
    python send_sms_alerts.py --send          # sends through Africa's Talking

Settings come from environment variables (never put the API key in the code or in GitHub):
    AT_USERNAME   "sandbox" for testing (messages appear only in the Africa's Talking simulator)
    AT_API_KEY    the API key of that app
    AT_SENDER_ID  optional, only if an approved sender ID exists
"""
import argparse
import os
import sys

import subscribers
from sokoradar_data import CROPS, county_alerts, month_sw

SMS_MAX = 160


def message_for(county):
    rows = county_alerts(county, horizon=1)
    if not rows:
        return None
    head = f"SokoRadar {county} {month_sw(rows[0]['target_month'])}: ONYO bei inaweza kupanda >15%: "
    parts = [f"{CROPS[r['commodity']][0]} KES {r['forecast_price_kes']:.0f} "
             f"({r['range_low_kes']:.0f}-{r['range_high_kes']:.0f})" for r in rows]
    msg = head + ", ".join(parts) + "."
    while len(msg) > SMS_MAX and len(parts) > 1:          # keep it to one SMS
        parts.pop()
        msg = head + ", ".join(parts) + " na zaidi."
    return msg


def main():
    ap = argparse.ArgumentParser(description="Send SokoRadar alert SMS to subscribers")
    ap.add_argument("--send", action="store_true", help="really send (default: dry run)")
    args = ap.parse_args()

    subs = subscribers.load()
    if not subs:
        sys.exit("No subscribers yet. Subscribe through the USSD menu (option 3) first.")

    sms = None
    if args.send:
        import africastalking
        user, key = os.environ.get("AT_USERNAME", "sandbox"), os.environ.get("AT_API_KEY")
        if not key:
            sys.exit("Set AT_API_KEY first (and AT_USERNAME, 'sandbox' for testing).")
        africastalking.initialize(user, key)
        sms = africastalking.SMS
        print(f"Sending as Africa's Talking user '{user}'"
              + (" (sandbox: messages show in the simulator only)" if user == "sandbox" else ""))

    sent = quiet = 0
    for s in subs:
        msg = message_for(s["county"])
        if msg is None:
            quiet += 1
            continue
        print(f"{s['phone']} [{s['county']}] ({len(msg)} chars): {msg}")
        if sms:
            sender = os.environ.get("AT_SENDER_ID")
            print("   ", sms.send(msg, [s["phone"]], sender) if sender else sms.send(msg, [s["phone"]]))
        sent += 1
    print(f"{'Sent' if sms else 'Would send'} {sent} SMS; {quiet} subscriber(s) had no alert this month.")


if __name__ == "__main__":
    main()
