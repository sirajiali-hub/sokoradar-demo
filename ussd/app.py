"""SokoRadar USSD service for Africa's Talking.

Africa's Talking calls POST /ussd with: sessionId, serviceCode, phoneNumber, text.
We reply in plain text starting with "CON " (menu) or "END " (answer).

Run locally:   python app.py            (then open http://localhost:5000 to check it is up)
Production:    gunicorn app:app         (Render, Hugging Face Spaces, Railway ...)
"""
import os

from flask import Flask, request

import menu
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


@app.get("/")
def health():
    df = load()
    return {"status": "ok", "data_file": str(DATA_FILE), "forecast_from": str(df["origin_month"].max()),
            "rows": int(len(df))}


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
