"""Fetch overnight lows for Florida cities and write status.json.

Run hourly by GitHub Actions. The website reads status.json, so no matter
how many people visit, the weather API only sees 24 requests a day.

Only the Open-Meteo forecast is allowed to fail the run. Everything else
(iNaturalist, the preview image, Bluesky) sits in its own try/except, logs
the problem and carries on.

Bluesky: when the answer flips from NO to YES (at most once every 12 hours)
the script posts to the lab account, in English with a Spanish reply.
Needs the Actions secrets BSKY_HANDLE and BSKY_APP_PASSWORD; without them it
skips quietly. Set DRY_RUN=true (the "dry_run" box when you run the workflow
by hand) to print the post instead of sending it.
"""
import json
import os
import shutil
import time
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STATUS = ROOT / "status.json"
FALLS = ROOT / "falls.json"
PER_PAGE = 200   # iNaturalist's maximum page size
MAX_PAGES = 25   # 5,000 reports; keeps the hourly job well under 2 minutes
INAT_PROJECT = "are-iguanas-falling"  # iNaturalist project slug
USER_AGENT = "are-iguanas-falling/1.0 (Stroud Lab, Georgia Tech; https://jameststroud.github.io/are-iguanas-falling/)"

SITE_URL = "https://jameststroud.github.io/are-iguanas-falling/"
BSKY_HOST = "https://bsky.social"
POST_GAP = timedelta(hours=12)  # never post more often than this

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


# Forecast points for the temperature-coloured map: a 0.35° grid of points inside the
# Florida outline used in index.html, plus four along the Keys. Generated once; the
# page interpolates between them.
GRID = [
    (25.2, -80.95), (25.55, -80.95), (25.55, -80.6), (25.9, -81.65), (25.9, -81.3), (25.9, -80.95),
    (25.9, -80.6), (25.9, -80.25), (26.25, -81.65), (26.25, -81.3), (26.25, -80.95), (26.25, -80.6),
    (26.25, -80.25), (26.6, -82.0), (26.6, -81.65), (26.6, -81.3), (26.6, -80.95), (26.6, -80.6),
    (26.6, -80.25), (26.95, -82.35), (26.95, -82.0), (26.95, -81.65), (26.95, -81.3), (26.95, -80.95),
    (26.95, -80.6), (26.95, -80.25), (27.3, -82.35), (27.3, -82.0), (27.3, -81.65), (27.3, -81.3),
    (27.3, -80.95), (27.3, -80.6), (27.3, -80.25), (27.65, -82.35), (27.65, -82.0), (27.65, -81.65),
    (27.65, -81.3), (27.65, -80.95), (27.65, -80.6), (28.0, -82.7), (28.0, -82.35), (28.0, -82.0),
    (28.0, -81.65), (28.0, -81.3), (28.0, -80.95), (28.0, -80.6), (28.35, -82.7), (28.35, -82.35),
    (28.35, -82.0), (28.35, -81.65), (28.35, -81.3), (28.35, -80.95), (28.35, -80.6), (28.7, -82.35),
    (28.7, -82.0), (28.7, -81.65), (28.7, -81.3), (28.7, -80.95), (29.05, -82.7), (29.05, -82.35),
    (29.05, -82.0), (29.05, -81.65), (29.05, -81.3), (29.05, -80.95), (29.4, -83.05), (29.4, -82.7),
    (29.4, -82.35), (29.4, -82.0), (29.4, -81.65), (29.4, -81.3), (29.75, -85.15), (29.75, -83.4),
    (29.75, -83.05), (29.75, -82.7), (29.75, -82.35), (29.75, -82.0), (29.75, -81.65), (29.75, -81.3),
    (30.1, -85.5), (30.1, -85.15), (30.1, -84.8), (30.1, -84.45), (30.1, -84.1), (30.1, -83.75),
    (30.1, -83.4), (30.1, -83.05), (30.1, -82.7), (30.1, -82.35), (30.1, -82.0), (30.1, -81.65),
    (30.45, -87.25), (30.45, -86.9), (30.45, -86.55), (30.45, -86.2), (30.45, -85.85), (30.45, -85.5),
    (30.45, -85.15), (30.45, -84.8), (30.45, -84.45), (30.45, -84.1), (30.45, -83.75), (30.45, -83.4),
    (30.45, -83.05), (30.45, -82.7), (30.45, -82.35), (30.45, -82.0), (30.45, -81.65), (30.8, -87.25),
    (30.8, -86.9), (30.8, -86.55), (30.8, -86.2), (30.8, -85.85), (30.8, -85.5), (30.8, -85.15),
    (24.56, -81.78), (24.66, -81.45), (24.72, -81.05), (24.92, -80.63),
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


def fetch_grid():
    """Overnight low at every GRID point (same window as the cities: next two nights)."""
    out = []
    for i in range(0, len(GRID), 100):  # Open-Meteo takes many points per call; 2 calls
        chunk = GRID[i:i + 100]
        url = (
            "https://api.open-meteo.com/v1/forecast"
            f"?latitude={','.join(str(p[0]) for p in chunk)}"
            f"&longitude={','.join(str(p[1]) for p in chunk)}"
            "&daily=temperature_2m_min&temperature_unit=fahrenheit"
            "&timezone=America%2FNew_York&forecast_days=2"
        )
        data = get_json(url)
        if isinstance(data, dict):
            data = [data]
        for (lat, lon), loc in zip(chunk, data):
            out.append({"lat": lat, "lon": lon, "min": round(min(loc["daily"]["temperature_2m_min"]), 1)})
    return out


def season_start(now):
    """1 November of the current winter."""
    return f"{now.year if now.month >= 7 else now.year - 1}-11-01"


def fetch_fall_count(since):
    inat = (
        "https://api.inaturalist.org/v1/observations"
        f"?project_id={INAT_PROJECT}&d1={since}&per_page=0"
    )
    return {"count": get_json(inat)["total_results"], "since": since}


def is_public(obs):
    """Only plot records whose exact location is public. iNaturalist still returns a
    (randomised) location for obscured records, so check every privacy flag."""
    if obs.get("obscured"):
        return False
    if obs.get("geoprivacy") in ("obscured", "private"):
        return False
    if obs.get("taxon_geoprivacy") in ("obscured", "private"):
        return False
    return bool(obs.get("location"))


def fetch_falls(since, max_pages=MAX_PAGES):
    """All of this winter's project observations, paged politely (200 a page, 1 s apart).
    Returns the data for falls.json: the total count and the public points."""
    points, total, hidden, last_id = [], 0, 0, 0
    for page in range(max_pages):
        if page:
            time.sleep(1)
        url = (
            "https://api.inaturalist.org/v1/observations"
            f"?project_id={INAT_PROJECT}&d1={since}&per_page={PER_PAGE}"
            f"&order_by=id&order=asc&id_above={last_id}"
        )
        results = get_json(url).get("results", [])
        for obs in results:
            total += 1
            if not is_public(obs):
                hidden += 1
                continue
            lat, lon = (float(x) for x in obs["location"].split(","))
            points.append({
                "lat": round(lat, 2),
                "lon": round(lon, 2),
                "date": obs.get("observed_on") or (obs.get("created_at") or "")[:10],
                "url": obs.get("uri") or f"https://www.inaturalist.org/observations/{obs['id']}",
            })
        if len(results) < PER_PAGE:
            break
        last_id = results[-1]["id"]
    else:
        print(f"iNaturalist: stopped after {max_pages} pages")
    return {"since": since, "count": total, "hidden": hidden, "points": points}


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


# ---------- Bluesky ----------

def post_texts(city, low):
    """English post and Spanish reply. Each must stay under 300 characters."""
    t = js_round(low)
    en = (f"\U0001F98E\U0001F976 Are iguanas falling? YES. The forecast overnight low in {city} is {t}°F, "
          f"cold enough for iguanas to lose their grip. Seen one fall? Report it on iNaturalist. "
          f"Tonight's map: {SITE_URL}")
    es = (f"\U0001F98E\U0001F976 ¿Se caen las iguanas? SÍ. La mínima pronosticada para {city} es {t}°F, "
          f"suficiente frío para que las iguanas se suelten. ¿Viste una caer? Repórtala en iNaturalist. "
          f"Mapa de esta noche: {SITE_URL}")
    return en, es


IMAGE_ALT = ("A cartoon green iguana lying belly-up on the ground under a tree, with snow falling, "
             "next to the words: Are iguanas falling? YES.")


def link_facet(text, url):
    """Bluesky needs the link's position in UTF-8 bytes, not characters."""
    b = text.encode("utf-8")
    start = b.index(url.encode("utf-8"))
    return {"index": {"byteStart": start, "byteEnd": start + len(url.encode("utf-8"))},
            "features": [{"$type": "app.bsky.richtext.facet#link", "uri": url}]}


def xrpc(method, body=None, token=None, raw=None, content_type="application/json"):
    data = raw if raw is not None else json.dumps(body).encode("utf-8")
    headers = {"Content-Type": content_type, "User-Agent": USER_AGENT}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(f"{BSKY_HOST}/xrpc/{method}", data=data, headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def build_posts(city, low, now, blob=None):
    en, es = post_texts(city, low)
    stamp = now.isoformat().replace("+00:00", "Z")
    root = {"$type": "app.bsky.feed.post", "text": en, "createdAt": stamp, "langs": ["en"],
            "facets": [link_facet(en, SITE_URL)]}
    if blob is not None:
        root["embed"] = {"$type": "app.bsky.embed.images", "images": [
            {"alt": IMAGE_ALT, "image": blob, "aspectRatio": {"width": 1200, "height": 630}}]}
    reply = {"$type": "app.bsky.feed.post", "text": es, "createdAt": stamp, "langs": ["es"],
             "facets": [link_facet(es, SITE_URL)]}
    return root, reply


def post_to_bluesky(city, low, now):
    """Log in with the app password, upload og-yes.png, post in English, reply in Spanish."""
    handle = os.environ.get("BSKY_HANDLE", "").strip()
    password = os.environ.get("BSKY_APP_PASSWORD", "").strip()
    if not handle or not password:
        return False  # secrets not set: skip quietly
    session = xrpc("com.atproto.server.createSession", {"identifier": handle, "password": password})
    token, did = session["accessJwt"], session["did"]
    img = (ROOT / "og-yes.png").read_bytes()
    if len(img) > 1_000_000:
        raise ValueError("og-yes.png is over Bluesky's 1 MB image limit")
    blob = xrpc("com.atproto.repo.uploadBlob", token=token, raw=img, content_type="image/png")["blob"]
    root, reply = build_posts(city, low, now, blob)
    first = xrpc("com.atproto.repo.createRecord",
                 {"repo": did, "collection": "app.bsky.feed.post", "record": root}, token=token)
    ref = {"uri": first["uri"], "cid": first["cid"]}
    reply["reply"] = {"root": ref, "parent": ref}
    xrpc("com.atproto.repo.createRecord",
         {"repo": did, "collection": "app.bsky.feed.post", "record": reply}, token=token)
    print(f"Bluesky: posted {first['uri']}")
    return True


def should_post(previous_answer, answer, last_posted, now):
    """Only on a NO to YES flip, and at most once every 12 hours. Never an all-clear."""
    if previous_answer != "no" or answer != "yes":
        return False
    if last_posted:
        try:
            if now - datetime.fromisoformat(last_posted) < POST_GAP:
                return False
        except ValueError:
            pass
    return True


def previous_answer(previous):
    """The last run's answer. Older status.json files have no "answer" field, so work it out."""
    if previous.get("answer") in ("yes", "no"):
        return previous["answer"]
    try:
        low = min(c["min"] for c in previous["cities"])
        return "yes" if js_round(low) <= FALL else "no"
    except Exception:
        return None


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

    # Temperature-coloured map. If this fails, drop the old grid so the page falls
    # back to colouring from the eight cities rather than showing a stale grid.
    try:
        status["grid"] = fetch_grid()
    except Exception as e:  # never let the map grid break the forecast
        status.pop("grid", None)
        print(f"Map grid skipped: {e}")

    # Fallen-iguana reports. The counter on the page and the map markers both come
    # from this one fetch, so they always agree.
    since = season_start(now)
    try:
        falls = fetch_falls(since)
        falls["updated"] = now.isoformat()
        FALLS.write_text(json.dumps(falls, indent=1))
        status["falls"] = {"count": falls["count"], "since": since}
        print(f"iNaturalist: {falls['count']} reports, {len(falls['points'])} mapped, {falls['hidden']} hidden")
    except Exception as e:  # never let iNaturalist break the forecast
        print(f"iNaturalist reports skipped: {e}")
        try:
            status["falls"] = fetch_fall_count(since)
        except Exception as e2:
            print(f"iNaturalist count skipped: {e2}")

    try:
        update_preview_image(answer)
    except Exception as e:
        print(f"Preview image skipped: {e}")

    try:
        dry_run = os.environ.get("DRY_RUN", "").strip().lower() in ("1", "true", "yes")
        flip = should_post(previous_answer(previous), answer, previous.get("last_posted"), now)
        if dry_run:
            root, reply = build_posts(coldest["n"], coldest["min"], now)
            print(f"Bluesky DRY RUN (nothing sent). Would post now: {flip} "
                  f"(previous answer {previous_answer(previous)}, now {answer}, last posted {previous.get('last_posted')})")
            print(f"--- post ({len(root['text'])} characters), image og-yes.png, alt: {IMAGE_ALT}\n{root['text']}")
            print(f"--- reply ({len(reply['text'])} characters)\n{reply['text']}")
        elif flip and post_to_bluesky(coldest["n"], coldest["min"], now):
            status["last_posted"] = now.isoformat()
    except Exception as e:  # never let Bluesky break the forecast
        msg = getattr(e, "code", "") or e
        print(f"Bluesky post skipped: {msg}")

    STATUS.write_text(json.dumps(status, indent=1))
    print(f"Coldest: {coldest['n']} {coldest['min']}F, answer: {answer}")


if __name__ == "__main__":
    main()
