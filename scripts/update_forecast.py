"""Fetch overnight lows for Florida cities and write status.json.

Run hourly by GitHub Actions. The website reads status.json, so no matter
how many people visit, the weather API only sees 24 requests a day.

Only the Open-Meteo forecast is allowed to fail the run. Everything else
(iNaturalist, the preview image) sits in its own try/except, logs the
problem and carries on.
"""
import json
import shutil
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STATUS = ROOT / "status.json"
INAT_PROJECT = "are-iguanas-falling"  # iNaturalist project slug
USER_AGENT = "are-iguanas-falling/1.0 (Stroud Lab, Georgia Tech; https://jameststroud.github.io/are-iguanas-falling/)"

# Must match FALL in index.html: a low of 44°F or below (after rounding) means YES
FALL = 44

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


def get_json(url, timeout=30):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)


def js_round(x):
    """Math.round() as the page does it (halves round up), so script and page agree."""
    return int((x + 0.5) // 1)


def fetch_forecast():
    url = (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={','.join(str(c[1]) for c in CITIES)}"
        f"&longitude={','.join(str(c[2]) for c in CITIES)}"
        "&daily=temperature_2m_min&temperature_unit=fahrenheit"
        "&timezone=America%2FNew_York&forecast_days=2"
    )
    data = get_json(url)
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
    return cities


def season_start(now):
    """1 November of the current winter."""
    return f"{now.year if now.month >= 7 else now.year - 1}-11-01"


def fetch_fall_count(since):
    inat = (
        "https://api.inaturalist.org/v1/observations"
        f"?project_id={INAT_PROJECT}&d1={since}&per_page=0"
    )
    return {"count": get_json(inat)["total_results"], "since": since}


def read_previous():
    try:
        return json.loads(STATUS.read_text())
    except Exception:
        return {}


def update_preview_image(answer):
    """Copy og-yes.png or og-no.png to og-image.png when the answer changes."""
    src = ROOT / f"og-{answer}.png"
    dst = ROOT / "og-image.png"
    if not dst.exists() or dst.read_bytes() != src.read_bytes():
        shutil.copyfile(src, dst)
        print(f"Preview image is now og-{answer}.png")


def main():
    now = datetime.now(timezone.utc)
    previous = read_previous()
    cities = fetch_forecast()  # the one call that is allowed to fail the run

    coldest = min(cities, key=lambda c: c["min"])
    answer = "yes" if js_round(coldest["min"]) <= FALL else "no"

    status = dict(previous)  # keep fields we don't touch this run
    status.update({
        "updated": now.isoformat(),
        "cities": cities,
        "answer": answer,
        "coldest": {"n": coldest["n"], "min": coldest["min"]},
    })

    try:
        status["falls"] = fetch_fall_count(season_start(now))
    except Exception as e:  # never let iNaturalist break the forecast
        print(f"iNaturalist count skipped: {e}")

    try:
        update_preview_image(answer)
    except Exception as e:
        print(f"Preview image skipped: {e}")

    STATUS.write_text(json.dumps(status, indent=1))
    print(f"Coldest: {coldest['n']} {coldest['min']}F, answer: {answer}")


if __name__ == "__main__":
    main()
