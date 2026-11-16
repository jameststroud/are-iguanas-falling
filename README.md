# Are iguanas falling?

A one-question website: is it cold enough tonight for iguanas to fall out of the trees in Florida?

From the Stroud Lab at Georgia Tech.

## What's in here

| File | What it does |
|---|---|
| `index.html` | Home page: YES/NO answer, cartoon iguana, Florida map, thermometer slider, iNaturalist report band and counter |
| `who.html` | "Who are we?" page. Lab roster is near the bottom of the file (`PEOPLE` and `ALUMNI`) |
| `assets/i18n.js` | Every piece of English and Spanish text on the site. Edit wording here |
| `assets/site.css` | Shared look (colours, fonts, nav, buttons) |
| `animations/` | Three reserve animations (field guide, thermal camera, night silhouette). Not linked from the site; visit `/animations/` to see them |
| `scripts/update_forecast.py` | Pulls overnight lows (Open-Meteo) and the iNaturalist fall count, writes `status.json` |
| `.github/workflows/update.yml` | Runs that script every hour |
| `inaturalist-description.md` | Text to paste into the iNaturalist project. Not used by the site |

`status.json` is created by the workflow; you never need to make it.

## Settings you might change

- Thresholds: top of the script in `index.html`. `FALL = 44` means a low of 44°F or below shows YES; `CHILLY = 55` slows the iguana down.
- iNaturalist project: `INAT_PROJECT` in `scripts/update_forecast.py`. The counter counts observations since 1 November each winter.
- Lab photos: upload images to `assets/people/` and add `photo:"assets/people/name.jpg"` to that person in `who.html`.

## Deploy

1. Upload everything to the repo (see the upload note below).
2. Settings → Pages → Build and deployment → Deploy from a branch → `main` / `(root)` → Save.
3. Settings → Actions → General → Workflow permissions → **Read and write permissions** → Save.
4. Actions tab → "Update iguana forecast" → Run workflow. This creates the first `status.json`.
5. The site appears at https://jameststroud.github.io/are-iguanas-falling/ within a few minutes.
6. Custom domain later: Settings → Pages → Custom domain, then point your DNS at GitHub Pages.

## Upload note

The browser uploader skips the hidden `.github` folder. Create `.github/workflows/update.yml` by hand: Add file → Create new file, type the full path `.github/workflows/update.yml` as the name (the slashes make the folders), and paste in the contents.
