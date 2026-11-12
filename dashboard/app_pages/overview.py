"""This month: where are price rises likely? A county map of spike alerts and the list of alerts."""
import streamlit as st

from src import charts, ui
from src.data import CORE, PHASE_TEXT, commodities, forecasts, month_name

ui.header("Where are food prices likely to jump?",
          "SokoRadar forecasts food prices in every Kenyan county 1 to 3 months ahead and warns when a rise above 15% "
          "is more likely than usual.")
ui.data_note()

fc = forecasts()
c1, c2, c3 = st.columns(3)
crop = c1.selectbox("Crop", commodities(fc), index=0)
ptype = c2.radio("Price", ["Retail", "Wholesale"], horizontal=True)
h = c3.radio("Months ahead", [1, 2, 3], horizontal=True)
d = fc[(fc["commodity"] == crop) & (fc["price_type"] == ptype) & (fc["horizon"] == h)]
target = month_name(d["target_month"].iloc[0]) if len(d) else ""

n_alert = int(d["spike_alert"].sum())
n_high = int(d["phase"].isin(["Alert", "Crisis"]).sum())
ui.kpis([
    ("Counties with a spike alert", f"{n_alert} of {len(d)}", "Chance of a rise above 15% is higher than the alert line."),
    ("High for the season now", f"{n_high} of {len(d)}", "ALPS label Alert or Crisis today: context, not an alert."),
    (f"Typical change by {target}", f"{d['forecast_change_pct'].median():+.1f}%", "Median forecast change across counties."),
])

left, right = st.columns([3, 2], gap="large")
with left:
    rows = {r["county"]: r for r in d.to_dict("records")}

    def hover(name, r):
        if r is None:
            return f"{name}: no forecast"
        return (f"<b>{name}</b><br>Now KES {r['price_kes']:.0f}{'' if r['price_is_real'] else ' (estimate)'}"
                f"<br>{target}: KES {r['forecast_price_kes']:.0f} ({r['range_low_kes']:.0f} to {r['range_high_kes']:.0f})"
                f"<br>Spike chance {r['spike_probability_pct']:.0f}%{'  ALERT' if r['spike_alert'] else ''}"
                f"<br>Season: {r['phase'] or 'not enough history'}")

    st.plotly_chart(charts.county_map(rows, lambda r: charts.ALERT_COLOR if r["spike_alert"] else charts.CALM_COLOR, hover),
                    width="stretch", config={"displayModeBar": False})
    st.markdown(charts.legend_html([("Spike alert", charts.ALERT_COLOR), ("No alert", charts.CALM_COLOR)]),
                unsafe_allow_html=True)

with right:
    st.subheader(f"Spike alerts for {target}")
    a = d[d["spike_alert"]].sort_values("spike_probability_pct", ascending=False)
    if a.empty:
        st.success("No county has a spike alert for this crop and month.")
    else:
        show = a.assign(range=a["range_low_kes"].round(0).astype(int).astype(str) + " to "
                        + a["range_high_kes"].round(0).astype(int).astype(str))
        show = show[["county", "price_kes", "forecast_price_kes", "range", "spike_probability_pct", "phase"]]
        st.dataframe(show, hide_index=True, width="stretch", height=430, column_config={
            "county": "County", "price_kes": st.column_config.NumberColumn("Now", format="%.0f"),
            "forecast_price_kes": st.column_config.NumberColumn("Forecast", format="%.0f"),
            "range": "Likely range",
            "spike_probability_pct": st.column_config.ProgressColumn("Spike chance", format="%.0f%%", min_value=0, max_value=100),
            "phase": "Season"})
        st.download_button("Download these alerts (CSV)", a.to_csv(index=False), f"sokoradar_alerts_{crop}_{ptype}_{h}m.csv",
                           "text/csv")
    st.caption("Prices in KES per kg. Likely range is the 80% range. Season is WFP's ALPS label: whether the price is "
               "already high for the time of year.")

if crop not in CORE:
    st.info("This crop is not one of the four core crops (maize, beans, sorghum, potatoes) that the results were tested on.")
