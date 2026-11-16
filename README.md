# Are iguanas falling?

A one-question website: is it cold enough tonight for iguanas to fall out of the trees in Florida?

From the Stroud Lab at Georgia Tech.

## What's in here

| File | What it does |
|---|---|
| `index.html` | Home page: YES/NO answer, "Share tonight's answer" button, cartoon iguana, Florida map, thermometer slider, iNaturalist report band and counter |
| `classroom.html` | Interactive lesson (Predict, Test, Record, Explain, Connect) with a collapsible, printable teacher guide. Linked as "Classroom" in every nav |
| `press.html` | Press kit for reporters: pitch, story angles, key facts with citations, bio, contact, downloadable graphics. Linked as "Press" in every footer |
| `assets/press/` | Press-kit downloads: link cards, square logo, transparent iguana, YES/NO screenshots (and your headshot, once uploaded) |
| `scripts/press_screenshots.js` | Optional dev tool that re-takes the two press screenshots with Playwright |
| `who.html` | "Who are we?" page. Lab roster is near the bottom of the file (`PEOPLE` and `ALUMNI`) |
| `assets/i18n.js` | Every piece of English and Spanish text on the site. Edit wording here |
| `assets/analytics.js` | GoatCounter visit counter and event tracking. Your GoatCounter code goes at the top |
| `assets/site.css` | Shared look (colours, fonts, nav, buttons) |
| `animations/` | Three reserve animations (field guide, thermal camera, night silhouette). Not linked from the site; visit `/animations/` to see them |
| `scripts/update_forecast.py` | Pulls overnight lows (Open-Meteo) and this winter's iNaturalist reports, writes `status.json` and `falls.json`, swaps the preview image, posts to Bluesky on a NO→YES flip |
| `falls.json` | This winter's fallen-iguana reports for the map: total count, number hidden for privacy, and public points (2-decimal coordinates, date, observation link) |
| `.github/workflows/update.yml` | Runs that script every hour |
| `inaturalist-description.md` | Text to paste into the iNaturalist project. Not used by the site |
| `og-yes.png`, `og-no.png` | 1200×630 link-preview cards (what Bluesky, X, iMessage etc. show) |
| `og-image.png` | The card the pages actually point to. The hourly job copies the YES or NO card here whenever the answer changes |
| `favicon.svg`, `apple-touch-icon.png` | Browser-tab and phone home-screen icons |
| `scripts/make_og.py` | Redraws the preview cards and icons. Only needed if you change the artwork or wording (see below) |
| `scripts/fonts/` | Archivo and Archivo Black (SIL Open Font License), used by `make_og.py` |

`status.json` and `falls.json` are written by the workflow; you never need to make them.

## Settings you might change

- Thresholds: top of the script in `index.html`. `FALL = 44` means a low of 44°F or below shows YES; `CHILLY = 55` slows the iguana down.
- iNaturalist project: `INAT_PROJECT` in `scripts/update_forecast.py`. The counter counts observations since 1 November each winter.
- Lab photos: upload images to `assets/people/` and add `photo:"assets/people/name.jpg"` to that person in `who.html`.

## Classroom page

- Wording (worksheet, questions, teacher guide, answer key): `assets/i18n.js`, keys starting `cl_` and `tg_`.
- Simulation settings: `MODEL SETTINGS` at the top of the script in `classroom.html`. The two anole CTmin values are real (Table 1 of the 2020 paper); the starting temperature, the two time constants and the iguana's 44°F falling point are teaching simplifications and the page says so.
- Printing: the two print buttons give a 4-page student worksheet, or the worksheet plus the teacher guide (which starts on a new page). Letter paper, no nav.
- If you change the time constants, re-run the simulation at 40°F and update the minutes in the answer key (`tg_k1`).

## Press kit

- Wording: `assets/i18n.js`, keys starting `press_`.
- **Headshot:** upload a square photo as `assets/press/stroud-headshot.jpg`, then in `press.html` change `const HAS_HEADSHOT=false;` to `true`.
- **Contact:** fill in the email and phone in `press.html` (search for `TODO(James)`).
- Downloads list: the `FILES` array near the bottom of `press.html`.
- `make_og.py` also writes the logo, the transparent iguana and copies of the link cards into `assets/press/`.

## Map of reported falls

Each hour the job fetches this winter's observations (since 1 November) from the iNaturalist project, 200 per page with a 1-second pause between pages, and writes `falls.json`. Obscured and private records (by the observer or because of the taxon) are never written with coordinates; they only add to the count. Public coordinates are rounded to 2 decimals (about 1 km).

On the home page each report is a small dark diamond on the Florida map (city forecasts stay round dots). Tapping one shows its date and a link to the observation. The counter and the markers both read `falls.json`, so they always agree, and a note under the map says how many reports are hidden for privacy. With no reports, there are no markers and no "Reported fall" legend entry.

## Visitor counts (GoatCounter)

GoatCounter counts visits without cookies or personal data. Until you add your code, nothing is loaded. If an ad blocker stops it, the site works as normal.

**Setting it up**

1. Sign up at https://www.goatcounter.com/signup (a free, donation-supported service). Pick a code, e.g. `iguanas`; your dashboard becomes `https://iguanas.goatcounter.com`.
2. In `assets/analytics.js`, change `var GOATCOUNTER_CODE = "GOATCOUNTER_CODE";` to your code, e.g. `var GOATCOUNTER_CODE = "iguanas";`. That one line covers every page.
3. Visit the site; pageviews appear in the dashboard within a few seconds (turn off your own ad blocker to check).

**Events counted** (they show up in the dashboard like pages):

| Event name | When |
|---|---|
| `share` | "Share tonight's answer" made an image |
| `cold-front` | "Send a cold front" button |
| `lang-switch-to-es` / `lang-switch-to-en` | Language button |
| `inaturalist-click` | Any link to iNaturalist |
| `press-download-<file>` | A press-kit download |
| `classroom-visit` | Someone opened the Classroom page |

To count another button or link, add `data-track="some-name"` to it.

**Numbers for NSF Broader Impacts reports**

- Quick totals: in the dashboard, set the date range to your reporting period. It shows total visits, visits per page (e.g. `/classroom.html`), the event counts above, and visitor locations by country and US state.
- Full export: in your GoatCounter site settings, use **Export** to download a ZIP of JSON files (you can set a start date). The CSV export only works if "Individual pageviews" is turned on in the site settings, so turn that on now if you'll want per-visit rows later.
- Useful lines for a report: total visits in the period, visits during named cold snaps, classroom page visits, share images made, and iNaturalist click-throughs (alongside the iNaturalist observation count on the home page).

## Cold-snap posts on Bluesky

When the answer flips from NO to YES, the hourly job posts to the lab's Bluesky account: an English post with the YES card attached, and a Spanish reply. It posts at most once every 12 hours and never posts an "all clear". The wording is in `post_texts()` in `scripts/update_forecast.py`.

**Setting it up**

1. Log in to the lab's Bluesky account → **Settings → Privacy and security → App passwords → Add App Password**. Name it `iguana-bot`, leave "Allow access to your direct messages" off, and copy the password it shows (you only see it once).
2. In this repo: **Settings → Secrets and variables → Actions → New repository secret**, twice:
   - `BSKY_HANDLE`: the account handle, e.g. `stroudlab.bsky.social` (no @)
   - `BSKY_APP_PASSWORD`: the app password from step 1
3. Test it: **Actions → Update iguana forecast → Run workflow**, tick **dry_run**, Run. Open the run's log: the "Bluesky DRY RUN" lines show exactly what would be posted. Nothing is sent.

Without the secrets the job skips posting quietly. To stop posting, delete either secret (or revoke the app password in Bluesky).

`status.json` fields used for this: `answer` (`"yes"`/`"no"`), `coldest` (`{n, min}`) and `last_posted` (time of the last post).

**X/Twitter** is not wired up. As of November 2026 the X API is pay-per-use with no free posting tier (creating a post costs credits, more if it contains a link), so it would need a paid account.

## Share button

"Share tonight's answer" draws a 1080×1350 PNG in the browser (code in `index.html`, under `Share tonight's answer`). It always uses the real forecast, never the what-if slider. On phones it opens the system share sheet; elsewhere it shows a preview with **Download image** and **Copy text**. The wording lives in `assets/i18n.js` under the `share_` keys.

## Link previews (Open Graph)

Every page has `og:` and `twitter:` tags pointing at `og-image.png`. Social sites cache previews, so a link shared yesterday may keep showing yesterday's answer for a while; that's expected.

To change the cards: edit the text in `og_card()` in `scripts/make_og.py`, then on your computer run

```
pip install resvg-py
python scripts/make_og.py
```

and commit the new PNGs. If you redraw the iguana in `index.html`, copy the new paths into `make_og.py` too.

## Deploy

1. Upload everything to the repo (see the upload note below).
2. Settings → Pages → Build and deployment → Deploy from a branch → `main` / `(root)` → Save.
3. Settings → Actions → General → Workflow permissions → **Read and write permissions** → Save.
4. Actions tab → "Update iguana forecast" → Run workflow. This creates the first `status.json`.
5. The site appears at https://jameststroud.github.io/are-iguanas-falling/ within a few minutes.
6. Custom domain later: Settings → Pages → Custom domain, then point your DNS at GitHub Pages.

## Upload note

The browser uploader skips the hidden `.github` folder. Create `.github/workflows/update.yml` by hand: Add file → Create new file, type the full path `.github/workflows/update.yml` as the name (the slashes make the folders), and paste in the contents.
