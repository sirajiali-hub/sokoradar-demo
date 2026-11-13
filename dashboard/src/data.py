"""Loads the data files made by prepare_data.py. Everything is cached, so pages open fast."""
import json
from pathlib import Path

import pandas as pd
import streamlit as st

DATA = Path(__file__).resolve().parents[2] / "data"
CORE = ["Dry Maize", "Beans Rosecoco", "Sorghum", "Red Irish Potatoes"]
PHASES = ["Normal", "Stress", "Alert", "Crisis"]
PHASE_COLOR = {"Normal": "#6b7d91", "Stress": "#f5c542", "Alert": "#ff8a3d", "Crisis": "#e5484d"}
PHASE_TEXT = {"Normal": "normal for the season", "Stress": "a little high for the season",
              "Alert": "high for the season", "Crisis": "very high for the season"}


@st.cache_data
def meta():
    return json.loads((DATA / "meta.json").read_text())


@st.cache_data
def forecasts():
    df = pd.read_csv(DATA / "forecasts.csv")
    for c in ("spike_alert", "price_is_real"):
        df[c] = df[c].astype(str).str.lower().isin(["true", "1"])
    df["phase"] = df["phase"].fillna("")
    for c in ("origin_month", "target_month"):
        df[c] = pd.PeriodIndex(df[c], freq="M")
    return df


@st.cache_data
def history():
    h = pd.read_csv(DATA / "history.csv.gz")
    h["month"] = pd.PeriodIndex(h["month"], freq="M").to_timestamp()
    return h


@st.cache_data
def counties():
    return pd.read_csv(DATA / "raw" / "counties.csv")


@st.cache_data
def geojson():
    return json.loads((DATA / "raw" / "ken_counties.geojson").read_text())


def commodities(df):
    """Core crops first, then the rest alphabetically."""
    rest = sorted(set(df["commodity"]) - set(CORE))
    return [c for c in CORE if c in set(df["commodity"])] + rest


def month_name(p):
    return p.strftime("%B %Y")
