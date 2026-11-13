"""On any phone: try the USSD menu and see the alert SMS, right in the browser.
The real service runs on Render and the Africa's Talking sandbox; this page uses the same menu code."""
import os
import sys
import tempfile
from html import escape
from pathlib import Path

import streamlit as st

from src import ui

USSD = Path(__file__).resolve().parents[2] / "ussd"
os.environ.setdefault("SOKORADAR_SUBSCRIBERS", os.path.join(tempfile.gettempdir(), "sokoradar_demo_subscribers.csv"))
sys.path.insert(0, str(USSD))
import menu                                   # noqa: E402  (the real USSD menu)
from send_sms_alerts import message_for       # noqa: E402
from sokoradar_data import counties           # noqa: E402
from i18n import LANGUAGES, TEXT              # noqa: E402

DEMO_PHONE = "+254700000000"

LANG_NAMES = ", ".join(TEXT[c]["name"] for c in LANGUAGES)
ui.header("On any phone: USSD and SMS", "Farmers and traders without a smartphone dial a short code to get the price "
          f"outlook and alerts for their county, in their language ({LANG_NAMES}). Try the same menu here.")

PHONE_CSS = """
<div style="max-width:320px;margin:auto;background:#05090e;border:2px solid #2b3a4d;border-radius:28px;padding:22px 16px 26px">
  <div style="background:#e8f5e9;color:#1b1b1b;border-radius:10px;padding:14px;min-height:260px;
              font-family:monospace;font-size:14px;line-height:1.45;white-space:pre-wrap">{screen}</div>
  <div style="color:#9aa5b1;text-align:center;font-size:12px;margin-top:10px">{status}</div>
</div>"""

if "ussd_text" not in st.session_state:
    st.session_state.ussd_text = None          # None = not dialled yet

left, right = st.columns([1, 1], gap="large")
with left:
    st.subheader("1. Dial the USSD code")
    text = st.session_state.ussd_text
    if text is None:
        reply, status = "CON Dial *384*1234# to start", "not connected"
    else:
        reply = menu.handle(text, DEMO_PHONE)
        status = "session ended" if reply.startswith("END") else "reply with a number"
    st.markdown(PHONE_CSS.format(screen=escape(reply[4:]), status=status), unsafe_allow_html=True)

    c1, c2 = st.columns([2, 1])
    if text is None or reply.startswith("END"):
        if c1.button("Dial \\*384\\*1234#", type="primary", width="stretch"):
            st.session_state.ussd_text = ""
            st.rerun()
    else:
        with c1.form("key", clear_on_submit=True, border=False):
            key = st.text_input("Your choice", max_chars=2, placeholder="type a number, e.g. 1", label_visibility="collapsed")
            if st.form_submit_button("Send", type="primary", width="stretch") and key.strip():
                st.session_state.ussd_text = key.strip() if text == "" else f"{text}*{key.strip()}"
                st.rerun()
    if c2.button("Hang up", width="stretch"):
        st.session_state.ussd_text = None
        st.rerun()
    st.caption("Counties come 8 per screen: 9 shows more, 0 goes back. Option 3 asks for consent before saving a number; "
               "on this page nothing is kept.")

with right:
    st.subheader("2. The alert SMS")
    c1, c2 = st.columns(2)
    county = c1.selectbox("Subscriber's county", counties(), index=counties().index("Garissa") if "Garissa" in counties() else 0)
    lang = c2.selectbox("Language", LANGUAGES, format_func=lambda c: TEXT[c]["name"])
    msg = message_for(county, lang)
    if msg:
        st.markdown(f"<div style='background:#1f3a5c;color:#e6ebf1;border-radius:14px;padding:12px 14px;max-width:360px'>"
                    f"{escape(msg)}</div>", unsafe_allow_html=True)
        st.caption(f"{len(msg)} characters: fits in one SMS (160).")
    else:
        st.info(f"No spike alert in {county} next month, so no SMS is sent.")
    st.markdown("""
**How it works**
1. A user subscribes through the USSD menu (option 3) and agrees to receive alerts.
2. When new forecasts arrive, a script sends each subscriber the spike alerts for their county.
3. The demo uses the Africa's Talking **sandbox**: messages appear in its online phone simulator, not on real phones.

**Languages:** the first screen asks for the language, and SMS come in the language chosen at sign up.
Gikuyu, Dholuo, Luluhya, Kikamba, Kalenjin and Kimeru switch on as soon as native speakers fill their column in
`ussd/translations.csv`.
""")
