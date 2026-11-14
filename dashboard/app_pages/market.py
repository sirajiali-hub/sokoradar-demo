"""Market check: one county and crop. Price now, the forecast with its range, the season label, the spike chance and why."""
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src import charts, location, ui
from src.data import PHASE_COLOR, PHASE_TEXT, commodities, forecasts, history, month_name
from src.results import FORECAST_ERROR

ui.header("Market check", "Pick a county and crop to see where the price is heading, how sure we are, and why.")
ui.data_note()

fc = forecasts()
c1, c2, c3 = st.columns(3)
crop = c1.selectbox("Crop", commodities(fc))
f1 = fc[fc["commodity"] == crop]
order = f1[f1["horizon"] == 1].sort_values("spike_probability_pct", ascending=False)["county"].drop_duplicates().tolist()
county = c2.selectbox("County", order, index=location.default_index(order, order[0]), help="Highest spike chance first.")
ptype = c3.radio("Price", sorted(f1[f1["county"] == county]["price_type"].unique()), horizontal=True)
s = f1[(f1["county"] == county) & (f1["price_type"] == ptype)].sort_values("horizon")
if s.empty:
    st.info("No forecast for this choice.")
    st.stop()

first, last = s.iloc[0], s.iloc[-1]
origin = month_name(first["origin_month"])
change = last["forecast_change_pct"]
direction = "rise" if change > 1 else ("fall" if change < -1 else "stay about the same")
alert_any = bool(s["spike_alert"].any())

# ---- headline ------------------------------------------------------------------------------------------------
phase = first["phase"]
season = f"It is **{PHASE_TEXT[phase]}** (ALPS {phase})." if phase else "There is not enough history for a season label."
st.markdown(f"#### {crop} ({ptype.lower()}) in {county}")
st.markdown(
    f"KES **{first['price_kes']:.0f}**/kg in {origin}{'' if first['price_is_real'] else ' (estimated)'}. {season} "
    f"The most likely path is to **{direction}** ({change:+.1f}% by {month_name(last['target_month'])}). "
    + ("**Spike alert:** a rise above 15% is more likely than usual." if alert_any else "No spike alert."))

cards = st.columns(1 + len(s))
cards[0].metric("Price now", f"KES {first['price_kes']:.0f}")
cards[0].caption("recorded in a market" if first["price_is_real"] else "estimated")
for col, r in zip(cards[1:], s.itertuples()):
    col.metric(f"{r.target_month.strftime('%b %Y')}", f"KES {r.forecast_price_kes:.0f}")
    col.caption(f"likely {r.range_low_kes:.0f} to {r.range_high_kes:.0f}"
                + ("  \n:red[**Spike alert**]" if r.spike_alert else ""))

# ---- charts --------------------------------------------------------------------------------------------------
hist = history()
hs = hist[(hist["county"] == county) & (hist["commodity"] == crop) & (hist["price_type"] == ptype)].sort_values("month")
left, right = st.columns([3, 2], gap="large")
with left:
    st.plotly_chart(charts.price_chart(hs, s), width="stretch", config={"displayModeBar": False})
    st.caption("The shaded band is the 80% range: in tests on unseen years, about 8 in 10 real prices fell inside it. "
               "Dark dots are prices recorded in a market; the grey line includes estimates.")
with right:
    fig = go.Figure()
    labels = [f"{h} month{'s' if h > 1 else ''}" for h in s["horizon"]]
    fig.add_trace(go.Bar(x=labels, y=s["spike_probability_pct"], name="spike chance",
                         marker_color=["#e5484d" if a else "#5b6b7e" for a in s["spike_alert"]]))
    if "alert_threshold_pct" in s:
        fig.add_trace(go.Scatter(x=labels, y=s["alert_threshold_pct"], mode="markers", name="alert line",
                                 marker=dict(symbol="line-ew-open", size=44, color="#e6ebf1", line=dict(width=2))))
    fig.update_layout(height=300, margin=dict(l=10, r=10, t=30, b=10), title="Chance of a rise above 15%",
                      yaxis_title="%", legend=dict(orientation="h", y=-0.2))
    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})
    st.caption("Red bars are above the alert line. An alert means higher risk, not a certain rise.")

with st.expander("Is the price high for the season? (ALPS score over time)"):
    st.plotly_chart(charts.alps_chart(hs), width="stretch", config={"displayModeBar": False})
    st.caption("WFP's ALPS method compares each price with its normal level for that time of year, learned from earlier "
               "months only. It shows where the price stands now; it is context, not a forecast.")

# ---- drivers -------------------------------------------------------------------------------------------------
st.subheader("What drives the forecast")
h = st.radio("Months ahead", list(s["horizon"]), horizontal=True, key="drv")
r = s[s["horizon"] == h].iloc[0]
if pd.notna(r.get("drivers_model_change_pct")):
    st.markdown(f"The drivers model expects **{r['drivers_model_change_pct']:+.1f}%** over {h} month{'s' if h > 1 else ''}, "
                f"starting from a typical change of {r['drivers_typical_change_pct']:+.1f}%. These inputs move it most:")
    for k in (1, 2, 3):
        push = r.get(f"driver_{k}_push_points")
        if pd.notna(push):
            st.markdown(f"- **{str(r[f'driver_{k}']).capitalize()}** ({r[f'driver_{k}_family']}): "
                        f"{'pushes the price up' if push > 0 else 'pushes the price down'} by {abs(push):.1f} points")
    st.caption("SHAP values show what the model leans on, not proof of cause. The drivers model is separate from the price "
               "forecast, so its number can differ.")
else:
    st.caption("No drivers for this forecast.")

# ---- where to buy --------------------------------------------------------------------------------------------
if isinstance(r.get("where_to_buy_county"), str):
    st.success(f"**Cheaper nearby:** {r['where_to_buy_county']}, KES {r['where_to_buy_price_kes']:.0f}/kg "
               f"({r['where_to_buy_saving_pct']:.0f}% cheaper, about {r['where_to_buy_km']:.0f} km). "
               "Check the Where to buy page to see if it pays after transport.")

st.caption(f"Typical forecast error in the 2015 to 2024 backtest: {FORECAST_ERROR[1]:.0f}%, {FORECAST_ERROR[2]:.0f}% and "
           f"{FORECAST_ERROR[3]:.0f}% at 1, 2 and 3 months, about the same as assuming no change.")
