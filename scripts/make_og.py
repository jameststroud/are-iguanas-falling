"""Render the social preview images and icons from SVG templates.

    pip install resvg-py
    python scripts/make_og.py

Writes (all committed to the repo, so the site never needs this script to run):
    og-yes.png, og-no.png         1200x630 link-preview cards
    og-image.png                  copy of og-no.png (the hourly job swaps it)
    favicon.svg                   browser-tab icon
    apple-touch-icon.png          180x180 home-screen icon

The iguana artwork below is copied from the cartoon scene in index.html. If you
redraw the iguana there, copy the new paths here too and re-run this script.
"""
import math
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FONTS = [str(p) for p in (Path(__file__).parent / "fonts").glob("*.ttf")]
URL_TEXT = "jameststroud.github.io/are-iguanas-falling"

# Colours from index.html: warm (NO) and cold (YES) palettes
WARM = dict(sky1="#ffd27a", sky2="#8fd3ef", ground="#7cb342", ig="#6fb53a", ig2="#3d7a22", belly="#c4df82")
COLD = dict(sky1="#c9e4f5", sky2="#7fa9c9", ground="#a9c3b0", ig="#8fb3a8", ig2="#4d6f6a", belly="#d3e3de")

# Centre of the iguana's bounding box (measured with getBBox() on index.html),
# used to flip it belly-up exactly the way the CSS "fall" animation does.
IG_CX, IG_CY = -59.86, -0.91


def crest_path():
    """Same spikes as the JavaScript in index.html."""
    d = ""
    for x in range(-48, 61, 9):
        y = -21 * math.sqrt(max(0, 1 - (x / 66) ** 2))
        h = 6 + 10 * (1 - abs(x - 20) / 80)
        d += f"M{x-4},{y+2:.2f}L{x},{y-h:.2f}L{x+4},{y+2:.2f}Z"
    return d


def iguana(c, eyes_closed=False):
    """The cartoon iguana, centred on its body, in its own coordinates."""
    lid = (f'<path d="M88,-12 C90,-16 97,-16 99,-12 C97,-8 90,-8 88,-12Z" fill="{c["ig2"]}"/>'
           if eyes_closed else "")
    return f'''
  <path d="M-50,-12 C-110,-12 -170,-4 -235,22 C-240,26 -236,30 -230,28 C-170,10 -110,12 -50,14 Z" fill="{c['ig']}"/>
  <g stroke="{c['ig2']}" stroke-width="5" stroke-linecap="round"><path d="M-82,-11 L-84,13"/><path d="M-112,-8 L-114,12"/><path d="M-142,-4 L-144,12"/><path d="M-172,3 L-174,14"/><path d="M-200,11 L-201,19"/></g>
  <path d="M-30,18 C-36,26 -44,30 -54,30 M-30,18 C-30,28 -34,32 -40,34" stroke="{c['ig2']}" stroke-width="7" stroke-linecap="round" fill="none"/>
  <path d="M40,16 C44,26 50,30 60,30 M40,16 C40,26 38,32 34,34" stroke="{c['ig2']}" stroke-width="7" stroke-linecap="round" fill="none"/>
  <ellipse cx="0" cy="0" rx="66" ry="21" fill="{c['ig']}"/>
  <ellipse cx="2" cy="10" rx="56" ry="9" fill="{c['belly']}"/>
  <path d="{crest_path()}" fill="{c['ig2']}"/>
  <path d="M64,10 C70,32 88,36 98,12 Z" fill="{c['belly']}" stroke="{c['ig2']}" stroke-width="1.5"/>
  <path d="M50,-15 C76,-26 102,-22 114,-9 C121,-2 118,7 108,9 C90,12 70,14 50,14 Z" fill="{c['ig']}"/>
  <circle cx="72" cy="5" r="7" fill="{c['belly']}" stroke="{c['ig2']}" stroke-width="1.5"/>
  <circle cx="93" cy="-10" r="4.5" fill="#2b1a0e"/><circle cx="94.5" cy="-11.5" r="1.4" fill="#fff"/>
  {lid}
  <path d="M112,-4 L117,-3" stroke="{c['ig2']}" stroke-width="2" stroke-linecap="round"/>'''


def scene(cold):
    """The 600x480 tree scene from index.html, as a <g>. Cold = fallen iguana and snow."""
    c = COLD if cold else WARM
    flakes = "".join(f'<circle cx="{(i*83) % 590 + 5}" cy="{(i*47) % 380 + 10}" r="{2 + i % 3}"/>' for i in range(26))
    pose = (f'translate(318,180) translate(-14,229) rotate(180 {IG_CX} {IG_CY})' if cold
            else 'translate(318,180)')
    sun = "" if cold else '<circle cx="505" cy="78" r="44" fill="#ffd54a"/><circle cx="505" cy="78" r="62" fill="#ffd54a" opacity=".25"/>'
    snow = f'<g fill="#fff">{flakes}</g>' if cold else ""
    return f'''
 <defs>
  <linearGradient id="sky{int(cold)}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{c['sky2']}"/><stop offset="1" stop-color="{c['sky1']}"/></linearGradient>
  <radialGradient id="crown{int(cold)}" cx=".4" cy=".35" r=".7"><stop offset="0" stop-color="#4f9a3a"/><stop offset="1" stop-color="#25602a"/></radialGradient>
 </defs>
 <rect width="600" height="480" fill="url(#sky{int(cold)})"/>
 {sun}{snow}
 <rect y="432" width="600" height="48" fill="{c['ground']}"/>
 <ellipse cx="300" cy="434" rx="320" ry="10" fill="#000" opacity=".08"/>
 <path d="M78,440 C92,360 96,260 108,150 L142,150 C140,260 136,360 150,440 Z" fill="#7a5532"/>
 <path d="M126,150 L142,150 C140,260 136,360 150,440 L134,440 C124,360 128,260 126,150Z" fill="#000" opacity=".12"/>
 <path d="M130,214 C230,200 380,198 540,204 L540,214 C380,212 230,214 134,232 Z" fill="#7a5532"/>
 <path d="M134,226 C230,210 380,210 540,212 L540,214 C380,214 230,216 134,232Z" fill="#000" opacity=".15"/>
 <g fill="url(#crown{int(cold)})"><circle cx="70" cy="110" r="60"/><circle cx="140" cy="70" r="66"/><circle cx="200" cy="120" r="52"/><circle cx="118" cy="140" r="50"/><circle cx="20" cy="60" r="50"/></g>
 <g fill="#3e8a35"><ellipse cx="530" cy="200" rx="22" ry="9" transform="rotate(-25 530 200)"/><ellipse cx="548" cy="214" rx="20" ry="8" transform="rotate(20 548 214)"/></g>
 <g transform="{pose}">{iguana(c, eyes_closed=cold)}</g>'''


def og_card(yes):
    bg = "#e9f4fb" if yes else "#fff6e0"
    big = "#2f7fc0" if yes else "#2f7d32"
    ink, soft = "#13261d", "#3d5246"
    answer = "YES." if yes else "NO."
    es = "¿Se caen las iguanas? SÍ." if yes else "¿Se caen las iguanas? NO."
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="630" viewBox="0 0 1200 630">
 <rect width="1200" height="630" fill="{bg}"/>
 <text x="64" y="128" font-family="Archivo Black" font-size="46" fill="{ink}">Are iguanas falling?</text>
 <text x="56" y="352" font-family="Archivo Black" font-size="210" letter-spacing="-4" fill="{big}">{answer}</text>
 <text x="66" y="424" font-family="Archivo" font-weight="700" font-size="32" fill="{soft}">{es}</text>
 <rect x="64" y="510" width="8" height="52" rx="4" fill="#ff7a2f"/>
 <text x="88" y="533" font-family="Archivo" font-weight="700" font-size="24" fill="{ink}">Tonight's forecast for Florida</text>
 <text x="88" y="562" font-family="Archivo" font-weight="400" font-size="24" fill="{soft}">{URL_TEXT}</text>
 <clipPath id="card"><rect x="620" y="99" width="540" height="432" rx="28"/></clipPath>
 <g clip-path="url(#card)"><g transform="translate(620,99) scale(.9)">{scene(yes)}</g></g>
 <rect x="620" y="99" width="540" height="432" rx="28" fill="none" stroke="#13261d" stroke-opacity=".12" stroke-width="2"/>
</svg>'''


def favicon_svg():
    """Iguana head on a sky-blue tile. Uses the head paths from the cartoon."""
    c = WARM
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="40 -46 92 92">
 <rect x="40" y="-46" width="92" height="92" rx="20" fill="#8fd3ef"/>
 <path d="M64,10 C70,32 88,36 98,12 Z" fill="{c['belly']}" stroke="{c['ig2']}" stroke-width="2"/>
 <path d="M40,-13 L50,-15 C76,-26 102,-22 114,-9 C121,-2 118,7 108,9 C90,12 70,14 50,14 L40,16 Z" fill="{c['ig']}"/>
 <path d="M42,-14 L46,-26 L50,-15 L54,-27 L58,-17 Z" fill="{c['ig2']}"/>
 <circle cx="72" cy="5" r="7" fill="{c['belly']}" stroke="{c['ig2']}" stroke-width="2"/>
 <circle cx="93" cy="-10" r="6" fill="#2b1a0e"/><circle cx="95" cy="-12" r="2" fill="#fff"/>
 <path d="M112,-4 L117,-3" stroke="{c['ig2']}" stroke-width="2.5" stroke-linecap="round"/>
</svg>'''


def render(svg, out, **kw):
    import resvg_py
    png = resvg_py.svg_to_bytes(svg_string=svg, font_files=FONTS, skip_system_fonts=True, **kw)
    Path(out).write_bytes(bytes(png))
    print("wrote", Path(out).relative_to(ROOT), f"({len(png)//1024} KB)")


def main():
    render(og_card(True), ROOT / "og-yes.png")
    render(og_card(False), ROOT / "og-no.png")
    if not (ROOT / "og-image.png").exists() or "--reset" in sys.argv:
        shutil.copyfile(ROOT / "og-no.png", ROOT / "og-image.png")
    fav = favicon_svg()
    (ROOT / "favicon.svg").write_text(fav)
    render(fav, ROOT / "apple-touch-icon.png", width=180, height=180)


if __name__ == "__main__":
    main()
