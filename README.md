# Are iguanas falling?

A one-question website: is it cold enough tonight for iguanas to fall out of the trees in Florida?

From the Stroud Lab at Georgia Tech.

## What's in here

| File | What it does |
|---|---|
| `index.html` | Home page: YES/NO answer, "Share tonight's answer" button, cartoon iguana, Florida map, thermometer slider, iNaturalist report band and counter |
| `press.html` | Press kit for reporters: pitch, story angles, key facts with citations, bio, contact, downloadable graphics. Linked as "Press" in every footer |
| `assets/press/` | Press-kit downloads: link cards, square logo, transparent iguana, YES/NO screenshots (and your headshot, once uploaded) |
| `scripts/press_screenshots.js` | Optional dev tool that re-takes the two press screenshots with Playwright |
| `who.html` | "Who are we?" page. Lab roster is near the bottom of the file (`PEOPLE` and `ALUMNI`) |
| `assets/i18n.js` | Every piece of English and Spanish text on the site. Edit wording here |
| `assets/site.css` | Shared look (colours, fonts, nav, buttons) |
| `animations/` | Three reserve animations (field guide, thermal camera, night silhouette). Not linked from the site; visit `/animations/` to see them |
| `scripts/update_forecast.py` | Pulls overnight lows (Open-Meteo) and the iNaturalist fall count, writes `status.json` |
| `.github/workflows/update.yml` | Runs that script every hour |
| `inaturalist-description.md` | Text to paste into the iNaturalist project. Not used by the site |
| `og-yes.png`, `og-no.png` | 1200×630 link-preview cards (what Bluesky, X, iMessage etc. show) |
| `og-image.png` | The card the pages actually point to. The hourly job copies the YES or NO card here whenever the answer changes |
| `favicon.svg`, `apple-touch-icon.png` | Browser-tab and phone home-screen icons |
| `scripts/make_og.py` | Redraws the preview cards and icons. Only needed if you change the artwork or wording (see below) |
| `scripts/fonts/` | Archivo and Archivo Black (SIL Open Font License), used by `make_og.py` |

`status.json` is created by the workflow; you never need to make it.

## Settings you might change

- Thresholds: top of the script in `index.html`. `FALL = 44` means a low of 44°F or below shows YES; `CHILLY = 55` slows the iguana down.
- iNaturalist project: `INAT_PROJECT` in `scripts/update_forecast.py`. The counter counts observations since 1 November each winter.
- Lab photos: upload images to `assets/people/` and add `photo:"assets/people/name.jpg"` to that person in `who.html`.

## Press kit

- Wording: `assets/i18n.js`, keys starting `press_`.
- **Headshot:** upload a square photo as `assets/press/stroud-headshot.jpg`, then in `press.html` change `const HAS_HEADSHOT=false;` to `true`.
- **Contact:** fill in the email and phone in `press.html` (search for `TODO(James)`).
- Downloads list: the `FILES` array near the bottom of `press.html`.
- `make_og.py` also writes the logo, the transparent iguana and copies of the link cards into `assets/press/`.

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
