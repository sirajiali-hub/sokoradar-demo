# SokoRadar: live demo

**An early warning system for food price shocks in Kenyan markets.**
Group 10, Moringa School Data Science Capstone, 2026. The analysis, notebooks and models are in the team repo: [emergingleader/Soko_Radar](https://github.com/emergingleader/Soko_Radar). This repo holds what users see: the dashboard and the phone service.

| Part | Where it runs | For whom |
|---|---|---|
| **Dashboard** (`dashboard/`) | Streamlit Community Cloud | County officers, NGOs, traders with a laptop or smartphone |
| **USSD and SMS** (`ussd/`) | Render, connected to the Africa's Talking sandbox | Farmers and traders on any phone |

Both read the same forecast table in `data/`, so nothing is computed while a user waits.

## The dashboard

1. **This month:** a county map of spike alerts for each crop, and the list of alerts.
2. **Market check:** one county and crop: price now, forecast with its 80% range, ALPS season label, spike chance, drivers.
3. **Where to buy:** nearby counties that are cheaper, and whether the saving survives transport for your vehicle and load.
4. **Does it work?:** every backtest result in plain words, with the limits.
5. **About:** the problem, the method, the data and the team.

Run it on your laptop from this folder:

```
pip install -r requirements.txt
streamlit run dashboard/app.py
```

## The phone service

See [`ussd/README.md`](ussd/README.md): the USSD menu in Kiswahili and English (price outlook, county alerts, SMS sign up) and the SMS alert script.

## Deploy

**Dashboard on Streamlit Community Cloud**
1. Sign in at share.streamlit.io with GitHub and click **Create app**.
2. Repository: this repo; branch: `main`; main file path: `dashboard/app.py`.
3. Under **Advanced settings**, choose Python 3.12. Click **Deploy**.

**USSD on Render**
1. Sign in at render.com with GitHub, click **New → Web Service** and choose this repo.
2. Root directory `ussd`; build command `pip install -r requirements.txt`; start command `gunicorn app:app`; plan Free.
3. In the Africa's Talking sandbox, create a USSD channel with the callback URL `https://<your Render address>/ussd`.
4. Free Render apps sleep after about 15 minutes: open the Render address in a browser a few minutes before a demo.

## Update the data

Run the team's two hand-over scripts, then `prepare_data.py`:

```
python sokoradar_forecast.py --data SokoRadar_County_2006_2024_long.csv --raw sokoradar_raw_data --out sokoradar_forecasts.csv
python sokoradar_alerts.py --data SokoRadar_County_2006_2024_long.csv --forecasts sokoradar_forecasts.csv --out sokoradar_final.csv
python prepare_data.py --final sokoradar_final.csv --forecasts sokoradar_forecasts.csv --prices SokoRadar_County_2006_2024_long.csv
```

Then commit the files in `data/` and `ussd/data/` and push; both apps update.

## Limits

* The data ends in December 2024, so the forecasts shown are for January to March 2025.
* Only about 7% of county prices were recorded in a market; all results are scored on those only.
* An alert means higher risk, not a certain rise. About half of sharp rises come with no alert.
* Transport costs use the government hire card and EPRA diesel prices; fuel use and driver costs are assumptions.

## Data credits

WFP market prices via HDX (CC BY IGO), World Bank, Ministry of Agriculture (KAMIS), KNBS, Central Bank of Kenya, EPRA, CHIRPS and NDVI via HDX, Ministry of Transport vehicle hire card, Ministry of Roads distance matrix.

*Forecasts are early warning, not certainty and not trading advice.*
