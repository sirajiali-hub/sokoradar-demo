"""Where to buy, after transport: the same costing as notebook 05_recommender (sections 2b and 7).

Cost of moving q kg over a road distance d, paid both ways:
    trips x ( max(2d x hire rate per km, minimum charge) + 2d x litres per km x diesel price + driver and handling )
    with trips = ceil(q / vehicle capacity).  A part-empty vehicle costs as much as a full one.
Hire rates are the government dry-hire card; fuel use and driver/handling are ASSUMPTIONS from the notebook.
"""
import numpy as np
import pandas as pd
import streamlit as st

from src.data import DATA, counties

MAX_KM = 200          # "nearby" = county centres within 200 km
ROAD_FACTOR = 1.3     # road km = straight-line km x 1.3 when the pair is not in the road distance file
MIN_GAIN = 0.05       # recommend only if it saves at least 5% of the local price after transport
RETURN = 2
# vehicle, card item, capacity kg, litres per km (assumed), driver and handling per trip KES (assumed)
VEHICLES = [("Pickup 4x2 (1 t)", 30, 1000, 0.12, 1000), ("Flat-bed truck 2.5-5 t", 1, 2500, 0.14, 1000),
            ("Flat-bed truck 5-7 t", 2, 5000, 0.20, 1000), ("Flat-bed truck 12 t", 4, 12000, 0.30, 1000),
            ("Flat-bed truck 20 t", 6, 20000, 0.38, 1000)]


@st.cache_data
def vehicles():
    card = pd.read_csv(DATA / "raw" / "govt_vehicle_hire_rates.csv")
    card = card[card["basic_unit"] == "KM"]
    rows = []
    for name, item, cap, l_km, fixed in VEHICLES:
        r = card[card["item"] == item].iloc[0]
        rows.append({"vehicle": name, "capacity_kg": cap, "l_per_km": l_km, "hire_per_km": float(r["dry_hire_private_kes"]),
                     "min_charge": float(r["min_charge_per_day_kes"]), "fixed": fixed})
    return pd.DataFrame(rows).set_index("vehicle")


@st.cache_data
def diesel():
    f = pd.read_csv(DATA / "raw" / "fuel_prices_by_county.csv")
    return f.set_index("county")["diesel_mean"].to_dict(), float(f["diesel_mean"].mean())


@st.cache_data
def neighbours():
    """All county pairs within MAX_KM (straight line), with road km where known."""
    c = counties()[["county", "center_lat", "center_lon"]]
    p = c.merge(c, how="cross", suffixes=("_a", "_b"))
    p = p[p["county_a"] != p["county_b"]]
    la1, lo1, la2, lo2 = (np.radians(p[k]) for k in ("center_lat_a", "center_lon_a", "center_lat_b", "center_lon_b"))
    h = np.sin((la2 - la1) / 2) ** 2 + np.cos(la1) * np.cos(la2) * np.sin((lo2 - lo1) / 2) ** 2
    p["km"] = 6371 * 2 * np.arcsin(np.sqrt(h))
    p = p[p["km"] <= MAX_KM][["county_a", "county_b", "km"]]
    road = pd.read_csv(DATA / "raw" / "county_road_distance.csv")[["county_a", "county_b", "road_km"]]
    road = pd.concat([road, road.rename(columns={"county_a": "county_b", "county_b": "county_a"})]).drop_duplicates(["county_a", "county_b"])
    p = p.merge(road, on=["county_a", "county_b"], how="left")
    p["road_known"] = p["road_km"].notna()
    p["road_km"] = p["road_km"].fillna(p["km"] * ROAD_FACTOR)
    return p


def cost_per_kg(road_km, qty_kg, vehicle, buyer_county):
    v = vehicles().loc[vehicle]
    prices, national = diesel()
    fuel = prices.get(buyer_county, national)
    trips = np.ceil(qty_kg / v["capacity_kg"])
    rt = np.asarray(road_km, dtype=float) * RETURN
    return trips * (np.maximum(rt * v["hire_per_km"], v["min_charge"]) + rt * v["l_per_km"] * fuel + v["fixed"]) / qty_kg


def options(fc, county, commodity, price_type, horizon, qty_kg, vehicle, real_only=True):
    """Nearby counties ranked by net saving after transport. Returns (local row, table)."""
    g = fc[(fc["commodity"] == commodity) & (fc["price_type"] == price_type) & (fc["horizon"] == horizon)]
    local = g[g["county"] == county]
    if local.empty:
        return None, pd.DataFrame()
    local = local.iloc[0]
    n = neighbours()
    c = n[n["county_a"] == county].merge(g.rename(columns={"county": "county_b"}), on="county_b")
    if real_only:
        c = c[c["price_is_real"]]
    if c.empty:
        return local, c
    c = c.assign(transport=cost_per_kg(c["road_km"], qty_kg, vehicle, county))
    c["price_gap"] = local["forecast_price_kes"] - c["forecast_price_kes"]
    c["net"] = c["price_gap"] - c["transport"]
    c["worth_it"] = c["net"] >= MIN_GAIN * local["forecast_price_kes"]
    return local, c.sort_values("net", ascending=False)
