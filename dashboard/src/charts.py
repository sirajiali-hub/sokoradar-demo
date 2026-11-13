"""Charts: the county map (drawn as filled shapes, so it needs no map tiles) and the price chart."""
import numpy as np
import pandas as pd
import plotly.graph_objects as go

from src.data import PHASE_COLOR, geojson

ALERT_COLOR, CALM_COLOR, NODATA_COLOR = "#e5484d", "#3a4a5c", "#1f2a37"


def _rings(geom):
    polys = geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]
    for poly in polys:
        yield poly[0]


def county_map(values, color_of, hover_of, height=560):
    """values: dict county -> row (or None). color_of(row) -> colour, hover_of(county, row) -> text."""
    fig = go.Figure()
    for f in geojson()["features"]:
        name = f["properties"]["county"]
        row = values.get(name)
        color = color_of(row) if row is not None else NODATA_COLOR
        text = hover_of(name, row)
        xs, ys = [], []
        for ring in _rings(f["geometry"]):
            xs += [p[0] for p in ring] + [None]
            ys += [p[1] for p in ring] + [None]
        fig.add_trace(go.Scatter(x=xs, y=ys, fill="toself", fillcolor=color, mode="lines",
                                 line=dict(color="#0e1621", width=0.8), hoverinfo="text", text=text,
                                 hoveron="fills", showlegend=False, name=name))
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False, scaleanchor="x", scaleratio=1)
    fig.update_layout(height=height, margin=dict(l=0, r=0, t=0, b=0), plot_bgcolor="rgba(0,0,0,0)",
                      paper_bgcolor="rgba(0,0,0,0)", hoverlabel=dict(bgcolor="#182433", font_color="#e6ebf1"))
    return fig


def legend_html(items):
    return " &nbsp; ".join(f"<span style='display:inline-block;width:12px;height:12px;background:{c};"
                           f"border-radius:2px;vertical-align:middle'></span> {t}" for t, c in items)


def price_chart(hist, rows, years=6):
    """Price history (real months marked) plus the forecast with its 80% range."""
    h = hist[hist["month"] >= hist["month"].max() - pd.DateOffset(years=years)]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=h["month"], y=h["price_kes"], mode="lines", name="price (estimated or recorded)",
                             line=dict(color="#7d8ea3", width=1.5)))
    real = h[h["observed"]]
    fig.add_trace(go.Scatter(x=real["month"], y=real["price_kes"], mode="markers", name="recorded in a market",
                             marker=dict(color="#e6ebf1", size=5)))
    if len(rows):
        last = h.iloc[-1]
        x = [last["month"]] + [r.target_month.to_timestamp() for r in rows.itertuples()]
        lo = [last["price_kes"]] + list(rows["range_low_kes"])
        hi = [last["price_kes"]] + list(rows["range_high_kes"])
        mid = [last["price_kes"]] + list(rows["forecast_price_kes"])
        fig.add_trace(go.Scatter(x=x + x[::-1], y=hi + lo[::-1], fill="toself", fillcolor="rgba(255,138,61,0.22)", mode="lines",
                                 line=dict(width=0), hoverinfo="skip", name="80% range"))
        fig.add_trace(go.Scatter(x=x, y=mid, mode="lines+markers", name="forecast", line=dict(color="#ff8a3d", width=2.5)))
    fig.update_layout(height=360, margin=dict(l=10, r=10, t=10, b=10), yaxis_title="KES per kg",
                      legend=dict(orientation="h", y=-0.15), hovermode="x unified")
    return fig


def alps_chart(hist, years=6):
    h = hist[(hist["month"] >= hist["month"].max() - pd.DateOffset(years=years)) & hist["alps"].notna()]
    phase = pd.cut(h["alps"], [-np.inf, 0.25, 1, 2, np.inf], right=False, labels=list(PHASE_COLOR))
    fig = go.Figure(go.Bar(x=h["month"], y=h["alps"], marker_color=[PHASE_COLOR[p] for p in phase],
                           hovertemplate="%{x|%b %Y}: score %{y:.2f}<extra></extra>"))
    for y, t in ((0.25, "Stress"), (1, "Alert"), (2, "Crisis")):
        fig.add_hline(y=y, line=dict(color="#5b6b7e", width=1, dash="dot"), annotation_text=t, annotation_position="right")
    fig.update_layout(height=220, margin=dict(l=10, r=40, t=10, b=10), yaxis_title="ALPS score", showlegend=False)
    return fig
