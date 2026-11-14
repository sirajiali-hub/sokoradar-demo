"""Does it work? Every result from the backtests, in plain words."""
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src import ui
from src.results import (FORECAST_ERROR, NEW_ALERTS, RANGE_INSIDE, RANGE_WIDTH, SPIKE, STRESS_JUMPS_CAUGHT, WFP,
                         WHERE_TO_BUY)

ui.header("Does it work?", "Each year from 2015 to 2024 was predicted using only earlier years, and every result is judged "
          "on prices recorded in a market.")

ui.kpis([
    ("Spike rises caught (1 month)", f"{SPIKE['caught'][1]:.0f}%", "Share of rises above 15% that had an alert."),
    ("Alerts followed by a rise", f"{SPIKE['right'][1]:.0f}%", f"About twice the normal rate of {SPIKE['base_rate_1m']:.0f}%."),
    ("Real prices inside the range", f"{RANGE_INSIDE[1]:.0f}% to {RANGE_INSIDE[3]:.0f}%", "Target 75% to 85%."),
    ("Warning time", f"{NEW_ALERTS['months_ahead']:.0f} months", "Before a market moves into Alert."),
])

st.subheader("1. The spike alert")
t = pd.DataFrame({"Months ahead": [1, 2, 3], "Rises caught %": [SPIKE["caught"][h] for h in (1, 2, 3)],
                  "Alerts followed by a rise %": [SPIKE["right"][h] for h in (1, 2, 3)]})
c1, c2 = st.columns([2, 3])
c1.dataframe(t, hide_index=True, width="stretch")
fig = go.Figure()
fig.add_trace(go.Bar(x=["1 month", "2 months", "3 months"], y=t["Rises caught %"], name="spike alert", marker_color="#e5484d"))
fig.add_trace(go.Bar(x=["1 month", "2 months", "3 months"], y=[STRESS_JUMPS_CAUGHT[h] for h in (1, 2, 3)],
                     name="ALPS Stress label", marker_color="#f5c542"))
fig.update_layout(height=260, barmode="group", title="Rises above 15% caught", yaxis_title="%",
                  margin=dict(l=10, r=10, t=40, b=10), legend=dict(orientation="h", y=-0.2))
c2.plotly_chart(fig, width="stretch", config={"displayModeBar": False})
st.markdown("The spike alert catches about half of sharp rises one month ahead. We also tested WFP's seasonal ALPS label "
            "as a second alarm: it caught only about 1 in 10 rises, close to chance, so it is shown as **context**, not as an alert.")

st.subheader("2. Warning before a market turns bad")
st.markdown(f"Of {NEW_ALERTS['cases']} times a market moved into ALPS Alert after a calm spell, the spike alert warned of "
            f"**{NEW_ALERTS['spike_alert']:.0f}%** and the ALPS Stress label of **{NEW_ALERTS['stress_label']:.0f}%**, "
            f"about {NEW_ALERTS['months_ahead']:.0f} months ahead. WFP's current ALPS only flags a market once prices are already high.")

st.subheader("3. Price ranges")
w = pd.DataFrame([(c, *v) for c, v in RANGE_WIDTH.items()], columns=["Crop", "1 month ±%", "2 months ±%", "3 months ±%"])
c1, c2 = st.columns(2)
c1.markdown(f"On years they had not seen (2017 to 2024), **{RANGE_INSIDE[1]:.0f}%, {RANGE_INSIDE[2]:.0f}% and "
            f"{RANGE_INSIDE[3]:.0f}%** of real prices fell inside the 80% range at 1, 2 and 3 months. Each crop has its own "
            "width: potato prices are much harder to predict.")
c2.dataframe(w, hide_index=True, width="stretch")

st.subheader("4. The price forecast")
st.markdown(f"Average error **{FORECAST_ERROR[1]:.1f}%, {FORECAST_ERROR[2]:.1f}% and {FORECAST_ERROR[3]:.1f}%** at 1, 2 and 3 "
            "months: about the same as assuming next month equals this month. Prices are hard to forecast from this data, "
            "which is why SokoRadar leads with the spike alert and an honest range rather than a single number.")

st.subheader("5. Earlier test on WFP market prices")
st.markdown(f"Before the county model, an ALPS early warning model was tested on 71 WFP market series: it caught "
            f"**{WFP['recall']}%** of Alert months with **{WFP['precision']}%** of warnings right (targets 70% and 50%), and warned "
            f"of **{WFP['warned_early']}%** of new alerts about {WFP['months_ahead']} months early.")
st.dataframe(pd.DataFrame(WFP["droughts"], columns=["Drought", "New alerts warned early", "New alerts"]), hide_index=True)
t26 = WFP["test_2025_26"]
st.caption(f"2011 uses a model trained without that drought. On 2025 to 2026, a calm period with only {t26['bad_months']} bad "
           f"months, it caught {t26['recall']}% with {t26['precision']}% of warnings right: a light check only.")

st.subheader("6. Where to buy")
st.markdown(f"The suggested county was really cheaper in {WHERE_TO_BUY['cheaper']} of cases, saving {WHERE_TO_BUY['saving']}. "
            "After transport, mainly full loads of 5 tonnes or more still pay. See the Where to buy page.")

st.subheader("Limits")
st.markdown("""
* An alert means higher risk, not a certain rise: about half of sharp rises come with no alert, often driven by things the
  data cannot see (floods, conflict, policy changes).
* Only about 7% of county prices were recorded in a market; all scores use those only.
* On 2025 to 2026, months the model never saw, it did at least as well: average error 8.9%, 10.6% and 12.4%, 56% of
  sharp rises caught one month ahead, and 81% to 88% of real prices inside the range.
""")
