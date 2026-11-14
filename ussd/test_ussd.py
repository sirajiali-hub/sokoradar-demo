"""Checks every language and menu path through the real web endpoint, and that every screen fits on a phone.

    python test_ussd.py
"""
import os
import tempfile

os.environ["SOKORADAR_SUBSCRIBERS"] = os.path.join(tempfile.mkdtemp(), "subscribers.csv")   # never touch the real list

import subscribers                     # noqa: E402
from app import app                    # noqa: E402
from i18n import LANGUAGES, TEXT       # noqa: E402
from send_sms_alerts import SMS_MAX, message_for   # noqa: E402
from sokoradar_data import counties    # noqa: E402

MAX_CHARS = 182
client = app.test_client()
PHONE = "+254700000001"
screens = 0


def dial(text):
    global screens
    r = client.post("/ussd", data={"sessionId": "t", "serviceCode": "*384*1#", "phoneNumber": PHONE, "text": text})
    body = r.get_data(as_text=True)
    assert r.status_code == 200, (text, r.status_code)
    assert body.startswith(("CON ", "END ")), (text, body)
    assert "kuna tatizo" not in body, f"{text!r} hit an error in the menu code (see the log above)"
    assert len(body) <= MAX_CHARS, f"{text!r} is {len(body)} chars:\n{body}"
    screens += 1
    return body


# every language has every word
keys = set(TEXT["en"])
for code in LANGUAGES:
    assert set(TEXT[code]) == keys, (code, keys ^ set(TEXT[code]))

first = dial("")
for k, code in enumerate(LANGUAGES, 1):
    assert TEXT[code]["name"] in first
assert dial(str(len(LANGUAGES) + 1)).startswith("END")
n = len(counties())

for k, code in enumerate(LANGUAGES, 1):
    L = str(k)
    assert dial(L).startswith("CON " + TEXT[code]["title"])
    for i in range(n):                                  # every county, crop and price type
        page, pos = divmod(i, 8)
        path = f"{L}*1" + "*9" * page + f"*{pos + 1}"
        assert dial(path).startswith("CON")
        for crop in "1234":
            for ptype in "12":
                assert dial(f"{path}*{crop}*{ptype}").startswith("END")
        assert dial(f"{L}*2" + "*9" * page + f"*{pos + 1}").startswith("END")
        msg = message_for(counties()[i], code)
        assert msg is None or len(msg) <= SMS_MAX, (code, counties()[i], len(msg), msg)
    assert "0. " + TEXT[code]["back"] in dial(f"{L}*1*9")
    assert dial(f"{L}*1*9*0") == dial(f"{L}*1")
    assert dial(f"{L}*7") == "END " + TEXT[code]["bad"]
    assert dial(f"{L}*1*99") == "END " + TEXT[code]["bad"]
    # sign up in this language, then leave
    assert TEXT[code]["yes"] in dial(f"{L}*3*1")
    assert dial(f"{L}*3*1*1").startswith("END " + TEXT[code]["subscribed"][:10])
    assert subscribers.load()[0]["lang"] == code
    assert dial(f"{L}*4") == "END " + TEXT[code]["unsubscribed"]
    assert dial(f"{L}*4") == "END " + TEXT[code]["was_not"]

# the welcome SMS fits in one message, and nothing is sent when no API key is set
import notify                          # noqa: E402
import voice                           # noqa: E402
for code in LANGUAGES:
    for c in counties():
        w = TEXT[code]["welcome"].format(county=c)
        assert len(w) <= SMS_MAX, (code, c, len(w))
assert not notify.enabled() or os.environ.get("AT_API_KEY")
# a copy by SMS: with sending switched on, price and alert answers are also texted, and the screen still fits
sent = []
real_send = notify.send_later
notify.send_later = lambda phone, message: sent.append((phone, message)) or True
for k, code in enumerate(LANGUAGES, 1):
    for i in range(n):
        page, pos = divmod(i, 8)
        pick = "*9" * page + f"*{pos + 1}"
        for crop in "1234":
            for ptype in "12":
                before = len(sent)
                s = dial(f"{k}*1{pick}*{crop}*{ptype}")
                assert s.endswith(TEXT[code]["sms_copy"]) == (len(sent) > before), s
        before = len(sent)
        s = dial(f"{k}*2{pick}")
        if len(sent) > before:
            assert s.endswith(TEXT[code]["sms_copy"]) and sent[-1][1].startswith("SokoRadar"), s
notify.send_later = real_send
assert sent and all(p == PHONE and len(m) <= SMS_MAX for p, m in sent), max(len(m) for _, m in sent)
copies = len(sent)
# voice: prepare a call, then the callback reads the alert in that language; an ended call gets an empty reply
for code in LANGUAGES:
    r = client.post("/voice/prepare", data={"phone": "+254700000999", "county": "Kitui", "lang": code}).get_json()
    assert r["ok"] and r["script"], r
    x = client.post("/voice", data={"isActive": "1", "destinationNumber": "+254700000999"}).get_data(as_text=True)
    if voice.recording("Kitui", code):                       # a real recording is played
        assert "<Play url=" in x and voice.recording_name("Kitui", code) in x, x
    else:                                                     # otherwise the computer voice reads the script
        assert x.startswith("<?xml") and "<Say>" in x and TEXT[code]["voice_bye"] in x, x
assert client.post("/voice", data={"isActive": "0"}).get_data(as_text=True) == ""
assert client.post("/voice/prepare", data={"phone": "abc"}).status_code == 400
assert client.get("/").get_json()["status"] == "ok"
print(f"All checks passed: {len(LANGUAGES)} languages, {n} counties, {screens} screens, "
      f"every screen within {MAX_CHARS} characters and every SMS within {SMS_MAX}; "
      f"{copies} answers also sent by SMS.")
