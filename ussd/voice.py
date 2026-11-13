"""Voice alerts: Africa's Talking phones a person and reads out the price alert for their county.

How a call works:
  1. voice_test.sh tells this app who will be called (POST /voice/prepare: phone, county, language),
     then asks Africa's Talking to place the call.
  2. When the person answers, Africa's Talking calls POST /voice (the callback URL set on the voice number),
     and this app replies with XML: <Say> lines that Africa's Talking speaks.
A subscriber who signed up through USSD is read the county and language they chose; anyone else gets the
prepared county and language, or Garissa in English.
"""
import os
import time
from pathlib import Path
from xml.sax.saxutils import escape

import subscribers
from i18n import LANGUAGES, month, t
from sokoradar_data import county_alerts

AUDIO = Path(__file__).parent / "audio"
PUBLIC_URL = os.environ.get("PUBLIC_URL", "https://sokoradar-ussd.onrender.com")
PENDING = {}                  # phone -> (county, lang, time prepared); kept in memory for 15 minutes
PENDING_MINUTES = 15


def prepare(phone, county, lang):
    PENDING[_norm(phone)] = (county, lang if lang in LANGUAGES else "en", time.time())


def _norm(phone):
    return "+" + "".join(ch for ch in str(phone) if ch.isdigit())


def who(numbers):
    """County and language for the person on the call."""
    for n in numbers:
        if not n:
            continue
        p = _norm(n)
        hit = PENDING.get(p)
        if hit and time.time() - hit[2] < PENDING_MINUTES * 60:
            return hit[0], hit[1]
        for s in subscribers.load():
            if _norm(s["phone"]) == p:
                return s["county"], s.get("lang") or "sw"
    return "Garissa", "en"


def script(county, lang):
    """The words of the call, as a list of sentences."""
    T = t(lang)
    rows = county_alerts(county, horizon=1)
    if not rows:
        return [T["voice_none"].format(county=county), T["voice_bye"]]
    lines = [T["voice_hello"].format(county=county, month=month(lang, rows[0]["target_month"]))]
    for r in rows:
        lines.append(T["voice_item"].format(crop=T["crops"][r["commodity"]], price=round(r["forecast_price_kes"]),
                                            low=round(r["range_low_kes"]), high=round(r["range_high_kes"])))
    lines.append(T["voice_bye"])
    return lines


def xml(lines):
    says = "".join(f"<Say>{escape(s)}</Say>" for s in lines)
    return f'<?xml version="1.0" encoding="UTF-8"?><Response>{says}</Response>'


def recording_name(county, lang):
    return f"{county.lower().replace(' ', '-')}_{lang}.mp3"


def recording(county, lang):
    """Path of a recorded voice alert for this county and language, or None."""
    p = AUDIO / recording_name(county, lang)
    return p if p.exists() else None


def call_xml(county, lang):
    """A real voice plays when we have one; otherwise the computer voice reads the script."""
    if recording(county, lang):
        return (f'<?xml version="1.0" encoding="UTF-8"?><Response>'
                f'<Play url="{PUBLIC_URL}/audio/{recording_name(county, lang)}"/></Response>')
    return xml(script(county, lang))
