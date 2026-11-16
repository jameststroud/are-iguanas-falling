"""Fetch overnight lows for Florida cities and write status.json.

Run hourly by GitHub Actions. The website reads status.json, so no matter
how many people visit, the weather API only sees 24 requests a day.
"""
import json
import urllib.request
from datetime import datetime, timezone

INAT_PROJECT = "are-iguanas-falling"  # iNaturalist project slug

# Order must match CITIES in index.html
CITIES = [
    ("Miami", 25.76, -80.19),
    ("Fort Lauderdale", 26.12, -80.14),
    ("West Palm Beach", 26.71, -80.05),
    ("Naples", 26.14, -81.79),
    ("Fort Myers", 26.64, -81.87),
    ("Key West", 24.56, -81.78),
    ("Tampa", 27.95, -82.46),
    ("Orlando", 28.54, -81.38),
]

url = (
    "https://api.open-meteo.com/v1/forecast"
    f"?latitude={','.join(str(c[1]) for c in CITIES)}"
    f"&longitude={','.join(str(c[2]) for c in CITIES)}"
    "&daily=temperature_2m_min&temperature_unit=fahrenheit"
    "&timezone=America%2FNew_York&forecast_days=2"
)

with urllib.request.urlopen(url, timeout=30) as r:
    data = json.load(r)

cities = []
for (name, lat, lon), loc in zip(CITIES, data):
    lows = loc["daily"]["temperature_2m_min"]
    cities.append({
        "n": name,
        "lat": lat,
        "lon": lon,
        "days": [{"date": d, "min": t} for d, t in zip(loc["daily"]["time"], lows)],
        "min": min(lows),
    })

# Fallen-iguana reports on iNaturalist since 1 November (the start of "this winter")
now = datetime.now(timezone.utc)
season_start = f"{now.year if now.month >= 7 else now.year - 1}-11-01"
falls = None
try:
    inat = (
        "https://api.inaturalist.org/v1/observations"
        f"?project_id={INAT_PROJECT}&d1={season_start}&per_page=0"
    )
    req = urllib.request.Request(inat, headers={"User-Agent": "are-iguanas-falling (Stroud Lab, Georgia Tech)"})
    with urllib.request.urlopen(req, timeout=30) as r:
        falls = {"count": json.load(r)["total_results"], "since": season_start}
except Exception as e:  # never let iNaturalist break the forecast
    print(f"iNaturalist count skipped: {e}")

status = {"updated": now.isoformat(), "cities": cities}
if falls is not None:
    status["falls"] = falls
with open("status.json", "w") as f:
    json.dump(status, f, indent=1)

coldest = min(cities, key=lambda c: c["min"])
print(f"Coldest: {coldest['n']} {coldest['min']}F")
