"""Backtest results shown in the app, copied from the notebooks (2015 to 2024 unless stated, real market prices only).
If a notebook is rerun and its numbers change, update them here."""

FORECAST_ERROR = {1: 9.0, 2: 12.3, 3: 14.5}              # 02_model_build: ARIMA average error %, about level with "no change"

SPIKE = {                                                 # 02_model_build / 07_alerts_aligned: rise above 15%
    "caught": {1: 47.8, 2: 44.5, 3: 34.4},
    "right": {1: 22.2, 2: 31.7, 3: 38.6},
    "base_rate_1m": 12.1,                                 # 05_recommender: share of real months with a spike, 1 month
}

NEW_ALERTS = {"cases": 347, "spike_alert": 50.7, "stress_label": 63.4, "months_ahead": 2.0}   # 07, Step 3
STRESS_JUMPS_CAUGHT = {1: 11.3, 2: 10.9, 3: 8.8}                                             # 07, Step 4

RANGE_INSIDE = {1: 78.1, 2: 80.4, 3: 81.9}               # 07, Step 5: tested 2017 to 2024 on unseen years
RANGE_WIDTH = {                                           # forecast plus or minus, %
    "Dry Maize": (15, 22, 28), "Sorghum": (18, 24, 27), "Beans Rosecoco": (16, 21, 24), "Red Irish Potatoes": (35, 51, 64),
}

WFP = {                                                   # 06_alerts: early warning on WFP market prices
    "recall": 72, "precision": 56, "warned_early": 75, "months_ahead": 2.2,
    "droughts": [("2011", 18, 21), ("2017", 15, 17), ("2022", 2, 4)],
    "test_2025_26": {"bad_months": 15, "recall": 60, "precision": 38},
}

WHERE_TO_BUY = {                                          # 05_recommender (with transport)
    "alerts_scored": 812, "cheaper": "93% to 96%", "saving": "about a quarter (about KES 16 per kg)",
    "same_as_cheapest_today": 92,
    "full_load_pays": {"Pickup 4x2 (1 t)": "29%", "Flat-bed truck 2.5-5 t": "53%", "Flat-bed truck 5-7 t": "68%",
                       "Flat-bed truck 12 t and 20 t": "up to about 85%"},
}
