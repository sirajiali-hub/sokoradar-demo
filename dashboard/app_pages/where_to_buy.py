"""Where to buy: is a nearby county cheaper, and does the saving survive the cost of the trip?"""
import streamlit as st

from src import location, transport, ui
from src.data import CORE, commodities, forecasts, month_name
from src.results import WHERE_TO_BUY

ui.header("Where to buy", "When a price rise is likely, is a nearby county cheaper, and is it still cheaper after transport?")
ui.data_note()

fc = forecasts()
c1, c2, c3 = st.columns(3)
crop = c1.selectbox("Crop", [c for c in commodities(fc) if c in CORE])
all_counties = sorted(fc["county"].unique())
county = c2.selectbox("Your county", all_counties, index=location.default_index(all_counties, "Nairobi"))
ptype = c3.radio("Price", ["Wholesale", "Retail"], horizontal=True)
c4, c5, c6 = st.columns(3)
vehicle = c4.selectbox("Vehicle", list(transport.vehicles().index), index=2)
cap = int(transport.vehicles().loc[vehicle, "capacity_kg"])
qty = c5.number_input("Quantity (kg)", min_value=50, max_value=40000, value=cap, step=50)
h = c6.radio("Buying in", [1, 2, 3], horizontal=True, format_func=lambda v: f"{v} month{'s' if v > 1 else ''}")
real_only = st.toggle("Only counties with a price recorded in a market", value=True,
                      help="Off: also uses estimated prices, which are less reliable.")

local, opts = transport.options(fc, county, crop, ptype, h, qty, vehicle, real_only)
if local is None:
    st.info("No forecast for this choice.")
    st.stop()

when = month_name(local["target_month"])
st.markdown(f"**{county}, {crop} ({ptype.lower()}), {when}:** forecast KES **{local['forecast_price_kes']:.0f}**/kg"
            + ("  (spike alert)" if local["spike_alert"] else ""))

if opts.empty:
    st.warning("No nearby county (within 200 km) has a recorded price this month. Turn off the switch above to use "
               "estimated prices.")
else:
    best = opts.iloc[0]
    if best["worth_it"]:
        st.success(f"**Buy in {best['county_b']}:** KES {best['forecast_price_kes']:.0f}/kg, {best['road_km']:.0f} km by road. "
                   f"Transport about KES {best['transport']:.1f}/kg, so you save about **KES {best['net']:.1f}/kg**, "
                   f"or **KES {best['net'] * qty:,.0f}** in total.")
    else:
        why = (f"saves only KES {best['net']:.1f}/kg" if best["net"] > 0 else f"costs KES {-best['net']:.1f}/kg more")
        st.info(f"**Stay local.** The best nearby option is {best['county_b']}, but after transport "
                f"(KES {best['transport']:.1f}/kg) it {why}. A bigger load or a bigger vehicle may change this.")
    show = opts.head(8)[["county_b", "forecast_price_kes", "price_is_real", "road_km", "price_gap", "transport", "net"]]
    st.dataframe(show, hide_index=True, width="stretch", column_config={
        "county_b": "County", "forecast_price_kes": st.column_config.NumberColumn("Forecast KES/kg", format="%.0f"),
        "price_is_real": "Recorded price", "road_km": st.column_config.NumberColumn("Road km", format="%.0f"),
        "price_gap": st.column_config.NumberColumn("Cheaper by", format="%.1f"),
        "transport": st.column_config.NumberColumn("Transport KES/kg", format="%.1f"),
        "net": st.column_config.NumberColumn("Net saving KES/kg", format="%.1f")})

st.divider()
st.subheader("What the backtest showed (2015 to 2024, real prices)")
st.markdown(f"""
* After a spike alert, the suggested county was really cheaper in **{WHERE_TO_BUY['cheaper']}** of {WHERE_TO_BUY['alerts_scored']} cases,
  saving **{WHERE_TO_BUY['saving']}** before transport.
* Choosing by the forecast adds nothing over "the cheapest nearby county today": they pick the same county
  {WHERE_TO_BUY['same_as_cheapest_today']}% of the time.
* **After transport, the load decides.** A full load still saves money in: """ +
            "; ".join(f"{k} {v}" for k, v in WHERE_TO_BUY["full_load_pays"].items()) +
            ". Small loads almost never pay, because a part-empty trip costs the same as a full one.")
st.caption("Transport uses the government vehicle hire card and EPRA diesel prices; fuel use and driver costs are assumed. "
           "Road distances cover 41 of 47 counties; other pairs use straight-line distance x 1.3. "
           "Best suited to bulk buyers such as NGOs, schools and traders.")
