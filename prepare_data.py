"""Builds the small data files the dashboard and the USSD app read. Run it after each new forecast.

    python prepare_data.py --final sokoradar_final.csv --forecasts sokoradar_forecasts.csv \
                           --prices SokoRadar_County_2006_2024_long.csv

Inputs
    --final      output of sokoradar_alerts.py --forecasts ...  (forecast, range, ALPS label, spike alert)
    --forecasts  output of sokoradar_forecast.py                (adds the drivers and where to buy details)
    --prices     the county price panel                          (price history for the charts)
Writes
    data/forecasts.csv          one row per series and horizon, everything the pages show
    data/history.csv.gz         monthly prices 2006 onwards, with the real/estimated flag and the ALPS score
    data/meta.json              when and from what the files were made
    ussd/data/sokoradar_final.csv   the same forecasts for the USSD app
"""
import argparse
import json
import shutil
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).parent
MIN_MONTHS = 36                         # same ALPS settings as sokoradar_alerts.py


def alps_all(prices):
    """ALPS score for every series and month (trend + 12 month dummies, fitted on earlier months only)."""
    P = prices.pivot(index="month", columns="series", values="price_kes").sort_index()
    t, mon = np.arange(len(P)), P.index.month
    X = np.column_stack([np.ones(len(P)), t] + [(mon == m).astype(float) for m in range(2, 13)])
    Y, out = P.values, np.full(P.shape, np.nan)
    for i in range(MIN_MONTHS, len(P)):
        beta, *_ = np.linalg.lstsq(X[:i], Y[:i], rcond=None)
        sd = (Y[:i] - X[:i] @ beta).std(axis=0, ddof=X.shape[1])
        out[i] = (Y[i] - X[i] @ beta) / sd
    return pd.DataFrame(out, index=P.index, columns=P.columns).rename_axis(index="month", columns="series")


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--final", required=True)
    ap.add_argument("--forecasts", required=True)
    ap.add_argument("--prices", required=True)
    a = ap.parse_args()

    final = pd.read_csv(a.final, encoding="utf-8-sig")
    fc = pd.read_csv(a.forecasts, encoding="utf-8-sig")
    key = ["series", "origin_month", "horizon"]
    extra = [c for c in fc.columns if c.startswith(("driver", "where_to_buy")) or c in ("alert_threshold_pct", "alert_message")]
    extra = [c for c in extra if c not in final.columns]
    df = final.merge(fc[key + extra], on=key, how="left")
    (HERE / "data").mkdir(exist_ok=True)
    df.to_csv(HERE / "data" / "forecasts.csv", index=False)

    prices = pd.read_csv(a.prices, parse_dates=["month"])
    prices["observed"] = prices["flag"].astype(str).str.startswith("Observed")
    prices["series"] = prices["county"] + " | " + prices["commodity"] + " | " + prices["price_type"]
    A = alps_all(prices).stack().rename("alps").reset_index()
    h = prices.merge(A, on=["month", "series"], how="left")
    h = h[["county", "commodity", "price_type", "month", "price_kes", "observed", "alps"]]
    h["month"] = h["month"].dt.strftime("%Y-%m")
    h["price_kes"], h["alps"] = h["price_kes"].round(2), h["alps"].round(2)
    h.to_csv(HERE / "data" / "history.csv.gz", index=False, compression="gzip")

    meta = {"forecast_from": str(df["origin_month"].max()), "price_data_to": h["month"].max(),
            "series": int(df["series"].nunique()), "made_from": [Path(a.final).name, Path(a.forecasts).name, Path(a.prices).name],
            "made_on": pd.Timestamp.now().strftime("%Y-%m-%d")}
    (HERE / "data" / "meta.json").write_text(json.dumps(meta, indent=1))

    (HERE / "ussd" / "data").mkdir(parents=True, exist_ok=True)
    shutil.copy(a.final, HERE / "ussd" / "data" / "sokoradar_final.csv")
    print(f"Saved data/forecasts.csv ({len(df):,} rows), data/history.csv.gz ({len(h):,} rows), data/meta.json, "
          f"ussd/data/sokoradar_final.csv. Forecasts from {meta['forecast_from']}.")


if __name__ == "__main__":
    main()
