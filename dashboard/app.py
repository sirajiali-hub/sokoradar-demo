"""SokoRadar dashboard. Run from the repo folder:  streamlit run dashboard/app.py"""
import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).parent))          # so pages can import src.*
from src import location  # noqa: E402

st.set_page_config(page_title="SokoRadar", page_icon="🌽", layout="wide")

pages = st.navigation([
    st.Page("app_pages/overview.py", title="This month", icon=":material/map:", default=True),
    st.Page("app_pages/market.py", title="Market check", icon=":material/query_stats:"),
    st.Page("app_pages/where_to_buy.py", title="Where to buy", icon=":material/local_shipping:"),
    st.Page("app_pages/phone.py", title="On any phone (USSD, SMS)", icon=":material/smartphone:"),
    st.Page("app_pages/results.py", title="Does it work?", icon=":material/fact_check:"),
    st.Page("app_pages/about.py", title="About", icon=":material/info:"),
])
with st.sidebar:
    st.markdown("## :orange[SokoRadar]")
    st.caption("Early warning of food price shocks in Kenyan counties. Group 10, Moringa School capstone.")
    location.sidebar()
pages.run()
