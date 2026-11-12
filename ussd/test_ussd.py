"""Checks every menu path through the real web endpoint, and that every screen fits on a phone.

    python test_ussd.py
"""
import os
import tempfile

os.environ["SOKORADAR_SUBSCRIBERS"] = os.path.join(tempfile.mkdtemp(), "subscribers.csv")   # never touch the real list

from app import app                    # noqa: E402
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
    assert len(body) <= MAX_CHARS, f"{text!r} is {len(body)} chars:\n{body}"
    screens += 1
    return body


assert dial("").startswith("CON SokoRadar")
n = len(counties())

# every county, every crop, both price types, through the pages (9 = next page)
for i in range(n):
    page, pos = divmod(i, 8)
    path = "1" + "*9" * page + f"*{pos + 1}"
    assert dial(path).startswith("CON")                      # crop menu
    for crop in "1234":
        for ptype in "12":
            assert dial(f"{path}*{crop}*{ptype}").startswith("END")
    assert dial("2" + "*9" * page + f"*{pos + 1}").startswith("END")      # alerts in that county

# paging back and forth, and wrong keys
assert "0. Nyuma" in dial("1*9")
assert dial("1*9*0") == dial("1")
assert dial("7").startswith("END Chaguo")
assert dial("1*99").startswith("END Chaguo")
assert dial("1*1*5").startswith("END Chaguo")

# sign up, then leave
assert "Ndiyo" in dial("3*1")
assert dial("3*1*1").startswith("END Umejiandikisha")
assert dial("4").startswith("END Umejiondoa")
assert dial("4").startswith("END Hukuwa")
assert dial("3*1*2").startswith("END Sawa")

# the health page
assert client.get("/").get_json()["status"] == "ok"

print(f"All checks passed: {n} counties, {screens} screens, every screen within {MAX_CHARS} characters.")
