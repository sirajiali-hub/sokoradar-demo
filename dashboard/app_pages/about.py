"""About: the problem, how SokoRadar works, the phone service, the data and the team."""
import streamlit as st

from src import ui
from src.data import meta

ui.header("About SokoRadar", "An early warning system for food price shocks in Kenyan markets. "
          "Group 10, Moringa School Data Science Capstone, 2026.")

st.markdown("""
#### The problem
Food price spikes hit poor households, farmers and pastoralists hardest. Today's tools report prices after they have risen,
so responses such as cash transfer top ups or reserve releases come late. SokoRadar asks: **can we see a price shock coming
early enough to act?**

#### What it gives each user
| Output | Question it answers |
|---|---|
| Price forecast | Where is this price heading over the next 1 to 3 months? |
| Price range | How far could it be from the forecast? (80% range) |
| Spike alert | Is a rise above 15% more likely than usual? |
| ALPS label | Is the price already high for the season? (Normal, Stress, Alert, Crisis) |
| Drivers | What is pushing the forecast up or down? |
| Where to buy | Which nearby county is cheaper, after transport? |

#### How it works
1. **Data:** a monthly price panel for 1,222 county series (47 counties, retail and wholesale), 2006 to 2024, with rainfall,
   vegetation, fuel and exchange rate data.
2. **Price forecast:** ARIMA on log prices, 1 to 3 months ahead.
3. **Spike alert:** a LightGBM model gives the chance of a rise above 15%; an alert fires above a fixed line.
4. **Drivers:** a second LightGBM model explained with SHAP.
5. **ALPS label and price ranges:** WFP's method for the season label, and ranges learned from past forecast errors per crop.
6. **Where to buy:** nearby counties with a recorded price, costed with road distance, fuel and vehicle hire.

#### On any phone: USSD and SMS
Farmers and traders without a smartphone can dial a USSD code to get the price outlook and alerts for their county in
Kiswahili, and sign up for alert SMS. The demo runs in the Africa's Talking sandbox.

#### Data sources
WFP market prices via HDX (CC BY IGO), World Bank, Ministry of Agriculture (KAMIS), KNBS, Central Bank of Kenya, EPRA fuel
prices, CHIRPS rainfall and NDVI via HDX, the Ministry of Transport vehicle hire card and the Ministry of Roads distance matrix.

#### Team
Zainabu (data), Thande and Frank (forecasting), Siraji (alerts and explainability), Tonny (deployment), Sam (product and impact).

*Forecasts are early warning, not certainty and not trading advice.*
""")
m = meta()
st.caption(f"Data files made on {m['made_on']} from {', '.join(m['made_from'])}.")
