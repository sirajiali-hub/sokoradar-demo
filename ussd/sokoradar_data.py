"""Reads the final SokoRadar table (forecasts + alerts) that the USSD menu and the SMS script use.

The table is the output of:
    python sokoradar_forecast.py --out sokoradar_forecasts.csv
    python sokoradar_alerts.py --forecasts sokoradar_forecasts.csv --out sokoradar_final.csv
Nothing is computed here: we only look up rows, so replies are instant.
"""
import os
from pathlib import Path

import pandas as pd

DATA_FILE = Path(os.environ.get("SOKORADAR_DATA", Path(__file__).parent / "data" / "sokoradar_final.csv"))

# crops in the menu, in this order: commodity in the data -> (Kiswahili, English)
CROPS = {
    "Dry Maize": ("Mahindi", "Maize"),
    "Beans Rosecoco": ("Maharagwe", "Beans"),
    "Sorghum": ("Mtama", "Sorghum"),
    "Red Irish Potatoes": ("Viazi", "Potatoes"),
}
PRICE_TYPES = {"Retail": ("Rejareja", "Retail"), "Wholesale": ("Jumla", "Wholesale")}
# ALPS label in Kiswahili (context, not an alert)
PHASE_SW = {"Normal": "Kawaida", "Stress": "Juu kidogo", "Alert": "Juu", "Crisis": "Juu sana"}
MONTH_SW = ["Jan", "Feb", "Mac", "Apr", "Mei", "Jun", "Jul", "Ago", "Sep", "Okt", "Nov", "Des"]

_cache = {"mtime": None, "df": None}


def load():
    """The latest forecasts, reloaded automatically when the CSV file changes."""
    mtime = DATA_FILE.stat().st_mtime
    if _cache["mtime"] != mtime:
        df = pd.read_csv(DATA_FILE, encoding="utf-8-sig")
        df = df[df["commodity"].isin(CROPS)]
        df = df[df["origin_month"] == df["origin_month"].max()]          # latest forecasts only
        df["spike_alert"] = df["spike_alert"].astype(str).str.lower().isin(["true", "1"])
        df["price_is_real"] = df["price_is_real"].astype(str).str.lower().isin(["true", "1"])
        _cache.update(mtime=mtime, df=df)
    return _cache["df"]


def counties():
    return sorted(load()["county"].unique())


def month_sw(yyyy_mm):
    y, m = str(yyyy_mm).split("-")[:2]
    return f"{MONTH_SW[int(m) - 1]} {y}"


def outlook(county, commodity, price_type, horizon=1):
    """One forecast row (a dict), or None."""
    df = load()
    r = df[(df["county"] == county) & (df["commodity"] == commodity) &
           (df["price_type"] == price_type) & (df["horizon"] == horizon)]
    return None if r.empty else r.iloc[0].to_dict()


def county_alerts(county, horizon=1):
    """Crops in this county with a spike alert, one row per crop (retail first when both alert)."""
    df = load()
    a = df[(df["county"] == county) & (df["horizon"] == horizon) & df["spike_alert"]]
    a = a.sort_values("price_type", key=lambda s: s.map({"Retail": 0, "Wholesale": 1}))
    a = a.drop_duplicates("commodity")
    order = list(CROPS)
    return sorted(a.to_dict("records"), key=lambda r: order.index(r["commodity"]))
