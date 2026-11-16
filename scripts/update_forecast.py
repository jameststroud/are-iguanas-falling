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
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STATUS = ROOT / "status.json"
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

    try:
        status["falls"] = fetch_fall_count(season_start(now))
    except Exception as e:  # never let iNaturalist break the forecast
        print(f"iNaturalist count skipped: {e}")

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
