"""SokoRadar USSD service for Africa's Talking.

Africa's Talking calls POST /ussd with: sessionId, serviceCode, phoneNumber, text.
We reply in plain text starting with "CON " (menu) or "END " (answer).
Voice: POST /voice is the callback for voice calls (the alert is read out); POST /voice/prepare says who will be called.

Run locally:   python app.py            (then open http://localhost:5000 to check it is up)
Production:    gunicorn app:app         (Render, Hugging Face Spaces, Railway ...)
"""
import os

from flask import Flask, request

import menu
import voice
from sokoradar_data import DATA_FILE, load

app = Flask(__name__)


@app.post("/ussd")
def ussd():
    text = request.values.get("text", "")
    phone = request.values.get("phoneNumber", "")
    try:
        reply = menu.handle(text, phone)
    except Exception:                       # never leave a user on a broken screen
        app.logger.exception("USSD error for text=%r", text)
        reply = "END Samahani, kuna tatizo. Jaribu baadaye. / Sorry, try later."
    return reply, 200, {"Content-Type": "text/plain; charset=utf-8"}


@app.post("/voice/prepare")
def voice_prepare():
    """Say who is about to be called: phone, county and language (sent by voice_test.sh just before the call)."""
    phone = request.values.get("phone", "").strip().replace(" ", "")
    phone = phone if phone.startswith("+") else "+" + phone
    county = request.values.get("county", "Garissa")
    lang = request.values.get("lang", "en")
    if not phone.lstrip("+").isdigit():
        return {"ok": False, "error": "phone must look like +254712345678"}, 400
    voice.prepare(phone, county, lang)
    return {"ok": True, "phone": phone, "county": county, "lang": lang,
            "script": voice.script(county, lang)}


@app.post("/voice")
def voice_callback():
    """Africa's Talking calls this when the person answers; we reply with the words to speak."""
    if request.values.get("isActive", "1") == "0":           # the call has ended: nothing to say
        return "", 200
    numbers = [request.values.get(k) for k in ("destinationNumber", "callerNumber", "clientDialedNumber")]
    try:
        county, lang = voice.who(numbers)
        body = voice.xml(voice.script(county, lang))
    except Exception:
        app.logger.exception("voice error")
        body = voice.xml(["Sorry, SokoRadar cannot read the alert right now. Goodbye."])
    return body, 200, {"Content-Type": "application/xml; charset=utf-8"}


@app.get("/")
def health():
    df = load()
    return {"status": "ok", "data_file": str(DATA_FILE), "forecast_from": str(df["origin_month"].max()),
            "rows": int(len(df))}


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
