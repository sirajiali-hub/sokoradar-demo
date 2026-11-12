"""The USSD menu. Africa's Talking sends every key press so far in `text` (e.g. "1*9*3*1*2"),
so the menu walks those choices from the start each time: no session storage is needed.

Replies start with "CON " (show a menu and wait) or "END " (show an answer and close).
Keep every screen short: USSD screens hold about 160 to 182 characters.
"""
import subscribers
from sokoradar_data import CROPS, PHASE_SW, PRICE_TYPES, counties, county_alerts, month_sw, outlook

PAGE = 8          # counties per screen; 9 = next page, 0 = previous page

MAIN = ("CON SokoRadar: bei za chakula\n"
        "1. Bei ijayo (Price outlook)\n"
        "2. Onyo kaunti yangu (Alerts)\n"
        "3. Jiandikishe SMS\n"
        "4. Jiondoe SMS")
BAD = "END Chaguo si sahihi. Jaribu tena. (Invalid choice)"


def handle(text, phone=""):
    steps = [s.strip() for s in text.split("*")] if text else []
    if not steps:
        return MAIN
    choice, rest = steps[0], steps[1:]
    flows = {"1": price_flow, "2": alerts_flow, "3": subscribe_flow, "4": unsubscribe_flow}
    if choice not in flows:
        return BAD
    return flows[choice](rest, phone)


# --------------------------------------------------------------------------- pickers
def pick_county(steps, title):
    """Walk the county pages. Returns (county, remaining steps, None) once picked,
    or (None, [], screen) while still choosing, or (None, [], BAD) on a wrong key."""
    names = counties()
    pages = (len(names) + PAGE - 1) // PAGE
    page = 0
    for i, s in enumerate(steps):
        if s == "9" and page < pages - 1:
            page += 1
        elif s == "0" and page > 0:
            page -= 1
        elif s.isdigit() and 1 <= int(s) <= PAGE and page * PAGE + int(s) <= len(names):
            return names[page * PAGE + int(s) - 1], steps[i + 1:], None
        else:
            return None, [], BAD
    shown = names[page * PAGE:(page + 1) * PAGE]
    lines = [f"CON {title}"] + [f"{k}. {n}" for k, n in enumerate(shown, 1)]
    if page < pages - 1:
        lines.append("9. Zaidi (More)")
    if page > 0:
        lines.append("0. Nyuma (Back)")
    return None, [], "\n".join(lines)


def pick_from(steps, options, title):
    """A simple numbered menu. options: list of (value, label)."""
    if not steps:
        return None, [], "\n".join([f"CON {title}"] + [f"{k}. {lab}" for k, (_, lab) in enumerate(options, 1)])
    s = steps[0]
    if s.isdigit() and 1 <= int(s) <= len(options):
        return options[int(s) - 1][0], steps[1:], None
    return None, [], BAD


CROP_OPTIONS = [(c, f"{sw} ({en})") for c, (sw, en) in CROPS.items()]
TYPE_OPTIONS = [(t, f"{sw} ({en})") for t, (sw, en) in PRICE_TYPES.items()]


# --------------------------------------------------------------------------- 1. price outlook
def price_flow(steps, phone):
    county, steps, screen = pick_county(steps, "Chagua kaunti (County):")
    if screen:
        return screen
    crop, steps, screen = pick_from(steps, CROP_OPTIONS, "Chagua zao (Crop):")
    if screen:
        return screen
    ptype, steps, screen = pick_from(steps, TYPE_OPTIONS, "Bei ya (Price type):")
    if screen:
        return screen
    return price_answer(county, crop, ptype)


def price_answer(county, crop, ptype):
    r = outlook(county, crop, ptype, horizon=1)
    if r is None:
        return f"END Hakuna data ya {CROPS[crop][0]} {county}. (No data)"
    now = f"KES {r['price_kes']:.0f}/kg" + ("" if r["price_is_real"] else " (makadirio)")
    lines = [
        f"END {CROPS[crop][0]}, {county} ({PRICE_TYPES[ptype][0].lower()})",
        f"{month_sw(r['origin_month'])}: {now}",
        f"{month_sw(r['target_month'])}: KES {r['forecast_price_kes']:.0f} "
        f"({r['range_low_kes']:.0f}-{r['range_high_kes']:.0f})",
    ]
    if isinstance(r.get("phase"), str) and r["phase"]:
        lines.append(f"Bei sasa: {PHASE_SW.get(r['phase'], r['phase'])} kwa msimu")
    if r["spike_alert"]:
        lines.append("ONYO: bei inaweza kupanda zaidi ya 15%")
    if isinstance(r.get("where_to_buy_county"), str) and r["where_to_buy_county"]:
        lines.append(f"Nafuu zaidi: {r['where_to_buy_county']}")
    return "\n".join(lines)


# --------------------------------------------------------------------------- 2. alerts in my county
def alerts_flow(steps, phone):
    county, steps, screen = pick_county(steps, "Onyo: chagua kaunti (County):")
    if screen:
        return screen
    return alerts_answer(county)


def alerts_answer(county):
    rows = county_alerts(county, horizon=1)
    if not rows:
        return f"END {county}: hakuna onyo la bei mwezi ujao. (No alerts next month)"
    month = month_sw(rows[0]["target_month"])
    lines = [f"END {county}, {month}", "ONYO: bei inaweza kupanda >15%:"]
    for r in rows:
        lines.append(f"- {CROPS[r['commodity']][0]}: KES {r['forecast_price_kes']:.0f} "
                     f"({r['range_low_kes']:.0f}-{r['range_high_kes']:.0f})")
    return "\n".join(lines)


# --------------------------------------------------------------------------- 3 and 4. SMS sign-up
def subscribe_flow(steps, phone):
    county, steps, screen = pick_county(steps, "SMS: chagua kaunti (County):")
    if screen:
        return screen
    ok, steps, screen = pick_from(steps, [(True, "Ndiyo, nakubali (Yes, I agree)"), (False, "Hapana (No)")],
                                  f"Kupokea SMS za onyo za {county}? Tutahifadhi namba yako kwa ajili hii tu.")
    if screen:
        return screen
    if not ok:
        return "END Sawa, hujajiandikisha. (Not subscribed)"
    if not phone:
        return "END Namba ya simu haikupatikana. (No phone number)"
    subscribers.add(phone, county)
    return f"END Umejiandikisha! Utapata SMS za onyo za {county}. Kujiondoe: chagua 4."


def unsubscribe_flow(steps, phone):
    removed = subscribers.remove(phone) if phone else 0
    if removed:
        return "END Umejiondoa. Hutapokea SMS tena. (Unsubscribed)"
    return "END Hukuwa umejiandikisha. (You were not subscribed)"
