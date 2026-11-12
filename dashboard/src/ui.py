"""Small layout helpers so every page looks the same."""
import streamlit as st

from src.data import meta, month_name

import pandas as pd


def header(title, subtitle):
    st.markdown("<div style='color:#ef6c00;font-weight:700;letter-spacing:.06em'>SOKORADAR · FOOD PRICE EARLY WARNING</div>",
                unsafe_allow_html=True)
    st.title(title)
    st.caption(subtitle)


def data_note():
    m = meta()
    origin = pd.Period(m["forecast_from"], freq="M")
    st.caption(f"Forecasts made from **{month_name(origin)}** prices (the latest month in the data), for the next 1 to 3 months. "
               "Only about 7% of county prices were recorded in a market; the rest are estimates. "
               "An alert means higher risk, not a certain price rise.")


def kpis(items):
    cols = st.columns(len(items))
    for col, (label, value, help_text) in zip(cols, items):
        col.metric(label, value, help=help_text)
