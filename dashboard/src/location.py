"""'Use my location': the browser shares the user's position (only if they allow it) and we pick the nearest county.
Nothing is saved; the county is kept only for this visit so every page opens on it."""
import math

import streamlit as st

from src.data import counties


def nearest_county(lat, lon):
    """The county whose centre is closest to the point."""
    c = counties()
    d = (c["center_lat"] - lat) ** 2 + ((c["center_lon"] - lon) * math.cos(math.radians(lat))) ** 2
    return c.loc[d.idxmin(), "county"]


def sidebar():
    """The switch in the sidebar. Sets st.session_state['my_county'] when the location is shared."""
    if not st.toggle("Use my location", key="use_location",
                     help="Your browser asks first. Used only to pick your county, never saved."):
        st.session_state.pop("my_county", None)
        return
    from streamlit_js_eval import get_geolocation
    loc = get_geolocation()
    if loc and "coords" in loc:
        county = nearest_county(loc["coords"]["latitude"], loc["coords"]["longitude"])
        st.session_state["my_county"] = county
        st.caption(f"You seem to be in **{county}** county.")
    elif loc is not None:
        st.session_state.pop("my_county", None)
        st.caption("Location not shared. Pick your county on each page.")


def default_index(options, fallback):
    """Position of the user's county in a list, else of the fallback county, else 0."""
    options = list(options)
    for c in (st.session_state.get("my_county"), fallback):
        if c in options:
            return options.index(c)
    return 0
