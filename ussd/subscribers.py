"""SMS subscribers: phone number, county and the date they agreed.

Phone numbers are personal data (Kenya's Data Protection Act 2019): we keep only what sending needs,
only after the user says yes, and the file is never committed to GitHub (see .gitignore).
For the capstone, use the Africa's Talking sandbox: it never sends to real phones.
"""
import csv
import os
from datetime import date
from pathlib import Path

FILE = Path(os.environ.get("SOKORADAR_SUBSCRIBERS", Path(__file__).parent / "data" / "subscribers.csv"))
FIELDS = ["phone", "county", "joined"]


def load():
    if not FILE.exists():
        return []
    with open(FILE, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _save(rows):
    FILE.parent.mkdir(parents=True, exist_ok=True)
    tmp = FILE.with_suffix(".tmp")
    with open(tmp, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)
    os.replace(tmp, FILE)


def add(phone, county):
    """Subscribe (or move) a phone number to one county."""
    rows = [r for r in load() if r["phone"] != phone]
    rows.append({"phone": phone, "county": county, "joined": date.today().isoformat()})
    _save(rows)


def remove(phone):
    rows = load()
    keep = [r for r in rows if r["phone"] != phone]
    _save(keep)
    return len(rows) - len(keep)
