#!/usr/bin/env python3
"""Genera city.svg: ciudad isométrica NEÓN animada.
Cada edificio es un día del año; cada bloque apilado es una contribución.
Sin dependencias externas (solo stdlib)."""
import colorsys
import datetime as dt
import json
import math
import os
import sys
import urllib.request

USER = os.environ.get("GH_USER", "vicente-arriagada-lost")
TOKEN = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
OUT = os.environ.get("OUT", "city.svg")
YEAR = int(os.environ.get("YEAR", dt.date.today().year))

S = 9.0            # tamaño de tile
BLOCK_H = 4.5      # alto de cada bloque (1 contribución)
MAX_BLOCKS = 12    # tope de bloques; si hay más, se escala
PAD = 0.1          # separación entre edificios
HUES = [180, 300, 55, 130, 265, 20]   # cian, magenta, amarillo, verde, violeta, naranja
WAVE = 7.0         # segundos que tarda la ola de luz en recorrer la ciudad

QUERY = """
query($u:String!,$f:DateTime!,$t:DateTime!){
  user(login:$u){
    contributionsCollection(from:$f,to:$t){
      contributionCalendar{
        totalContributions
        weeks{contributionDays{date contributionCount weekday}}
      }
    }
  }
}"""


def fetch():
    if not TOKEN:
        sys.exit("Falta GH_TOKEN o GITHUB_TOKEN")
    body = json.dumps({
        "query": QUERY,
        "variables": {"u": USER, "f": f"{YEAR}-01-01T00:00:00Z", "t": f"{YEAR}-12-31T23:59:59Z"},
    }).encode()
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=body,
        headers={"Authorization": f"bearer {TOKEN}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.load(r)
    if "errors" in data:
        sys.exit(f"Error GraphQL: {data['errors']}")
    return data["data"]["user"]["contributionsCollection"]["contributionCalendar"]


def hsl(h, s, l):
    r, g, b = colorsys.hls_to_rgb((h % 360) / 360, l / 100, s / 100)
    return "#%02x%02x%02x" % (round(r * 255), round(g * 255), round(b * 255))


def proj(i, j, z=0.0):
    return ((i - j) * S * 0.866, (i + j) * S * 0.5 - z)


def P(points):
    return " ".join(f"{x:.1f},{y:.1f}" for x, y in points)


def line(a, b):
    return f"M{a[0]:.1f},{a[1]:.1f}L{b[0]:.1f},{b[1]:.1f}"


def building(i, j, c, date, busiest, n_weeks):
    n = c if busiest <= MAX_BLOCKS else max(1, math.ceil(c / busiest * MAX_BLOCKS))
    h = n * BLOCK_H
    k = (i + 2 * j) % len(HUES)
    ht, hl, hr = HUES[k], HUES[(k + 2) % 6], HUES[(k + 4) % 6]   # cada cara con su color

    a, b = (i + PAD, j + PAD), (i + 1 - PAD, j + PAD)
    cc, d = (i + 1 - PAD, j + 1 - PAD), (i + PAD, j + 1 - PAD)

    left = [proj(*d), proj(*cc), proj(*cc, h), proj(*d, h)]
    right = [proj(*b), proj(*cc), proj(*cc, h), proj(*b, h)]
    top = [proj(*p, h) for p in (a, b, cc, d)]

    # líneas entre bloques (una por contribución)
    seps_l = "".join(line(proj(*d, z * BLOCK_H), proj(*cc, z * BLOCK_H)) for z in range(1, n))
    seps_r = "".join(line(proj(*b, z * BLOCK_H), proj(*cc, z * BLOCK_H)) for z in range(1, n))

    sw = "1.1"
    g = [f'<g><title>{date}: {c} contribution{"s" if c != 1 else ""}</title>']
    g.append(f'<polygon points="{P(left)}" fill="{hsl(hl,70,8)}" stroke="{hsl(hl,100,60)}" stroke-width="{sw}"/>')
    g.append(f'<polygon points="{P(right)}" fill="{hsl(hr,70,11)}" stroke="{hsl(hr,100,60)}" stroke-width="{sw}"/>')
    if n > 1:
        g.append(f'<path d="{seps_l}" stroke="{hsl(hl,100,60)}" stroke-opacity=".45" stroke-width=".7" fill="none"/>')
        g.append(f'<path d="{seps_r}" stroke="{hsl(hr,100,60)}" stroke-opacity=".45" stroke-width=".7" fill="none"/>')
    g.append(f'<polygon points="{P(top)}" fill="{hsl(ht,70,16)}" stroke="{hsl(ht,100,65)}" stroke-width="{sw}"/>')

    # capa de luz: contorno visible con destello que recorre las aristas
    outline = (
        f"M{P(top).replace(' ', 'L')}Z"
        + line(proj(*d), proj(*d, h)) + line(proj(*cc), proj(*cc, h)) + line(proj(*b), proj(*b, h))
        + line(proj(*d), proj(*cc)) + line(proj(*cc), proj(*b))
    )
    delay = i / max(1, n_weeks) * WAVE - WAVE
    g.append(
        f'<g class="wave" style="animation-delay:{delay:.2f}s">'
        f'<path class="flow" d="{outline}" stroke="{hsl(ht,100,82)}" stroke-width="1.5" fill="none" filter="url(#glow)"/></g>'
    )
    g.append("</g>")
    return "".join(g)


def main():
    cal = fetch()
    cells = []
    for wi, week in enumerate(cal["weeks"]):
        for d in week["contributionDays"]:
            cells.append((wi, d["weekday"], d["contributionCount"], d["date"]))

    total = cal["totalContributions"]
    active = sum(1 for c in cells if c[2] > 0)
    busiest = max((c[2] for c in cells), default=0) or 1
    n_weeks = len(cal["weeks"])

    # suelo: rejilla neón
    grid = "".join(
        "M" + "L".join(f"{x:.1f},{y:.1f}" for x, y in [proj(i, j), proj(i + 1, j), proj(i + 1, j + 1), proj(i, j + 1)]) + "Z"
        for i, j, c, _ in cells
    )

    bs = [building(i, j, c, date, busiest, n_weeks)
          for i, j, c, date in sorted(cells, key=lambda t: (t[0] + t[1], t[0])) if c > 0]

    # perímetro con luz recorriendo el borde de la ciudad
    per = [proj(0, 0), proj(n_weeks, 0), proj(n_weeks, 7), proj(0, 7)]
    perimeter = "M" + "L".join(f"{x:.1f},{y:.1f}" for x, y in per) + "Z"

    xs = [p[0] for p in per]
    ys = [p[1] for p in per]
    min_x, max_x = min(xs) - 30, max(xs) + 30
    min_y, max_y = min(ys) - MAX_BLOCKS * BLOCK_H - 30, max(ys) + 30
    w, h = max_x - min_x, max_y - min_y

    mono = "ui-monospace,SFMono-Regular,Menlo,Consolas,monospace"
    tx, ty = min_x + 18, max_y - 62

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="{min_x:.0f} {min_y:.0f} {w:.0f} {h:.0f}" width="100%" role="img" aria-label="Neon contribution city {YEAR}: {total} contributions">
<style>
.flow{{stroke-linecap:round;stroke-linejoin:round;stroke-dasharray:3 15;animation:flow 2.2s linear infinite}}
.wave{{animation:wave {WAVE}s ease-in-out infinite}}
.rim1{{stroke-dasharray:40 400;animation:rim 9s linear infinite}}
.rim2{{stroke-dasharray:40 400;animation:rim 9s linear infinite;animation-delay:-4.5s}}
@keyframes flow{{to{{stroke-dashoffset:-36}}}}
@keyframes wave{{0%,100%{{opacity:.3}}12%{{opacity:1}}32%{{opacity:.3}}}}
@keyframes rim{{to{{stroke-dashoffset:-440}}}}
@media (prefers-reduced-motion:reduce){{.flow,.wave,.rim1,.rim2{{animation:none}}}}
</style>
<defs>
<radialGradient id="bg" cx="50%" cy="45%" r="80%"><stop offset="0" stop-color="#220044"/><stop offset="1" stop-color="#0b0120"/></radialGradient>
<filter id="glow" x="-30%" y="-30%" width="160%" height="160%"><feGaussianBlur stdDeviation="1.4" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
</defs>
<rect x="{min_x:.0f}" y="{min_y:.0f}" width="{w:.0f}" height="{h:.0f}" rx="10" fill="url(#bg)"/>
<path d="{grid}" fill="#12002a" fill-opacity=".6" stroke="#5b2bb0" stroke-opacity=".55" stroke-width=".5"/>
<path d="{perimeter}" fill="none" stroke="#ff2bd6" stroke-opacity=".7" stroke-width="1.2" filter="url(#glow)"/>
<path class="rim1" d="{perimeter}" fill="none" stroke="#00f5ff" stroke-width="2.2" stroke-linecap="round" filter="url(#glow)"/>
<path class="rim2" d="{perimeter}" fill="none" stroke="#ffe600" stroke-width="2.2" stroke-linecap="round" filter="url(#glow)"/>
{"".join(bs)}
<g font-family="{mono}" filter="url(#glow)">
<text x="{tx:.0f}" y="{ty - 34:.0f}" font-size="6" letter-spacing="2" fill="#00f5ff">NEON CONTRIBUTION CITY {YEAR}</text>
<text x="{tx:.0f}" y="{ty - 8:.0f}" font-size="22" font-weight="700" fill="#ff2bd6">{total}</text>
<text x="{tx:.0f}" y="{ty + 4:.0f}" font-size="6" fill="#e9d5ff">contributions this year</text>
<text x="{tx:.0f}" y="{ty + 20:.0f}" font-size="6" fill="#ffe600">{active} active days · busiest day: {busiest}</text>
<text x="{tx:.0f}" y="{ty + 34:.0f}" font-size="5" fill="#00f5ff" opacity=".7">@{USER} · 1 block = 1 contribution</text>
</g>
</svg>
"""
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"OK -> {OUT} ({total} contribuciones, {active} días activos, máx {busiest}, {len(svg)//1024} KB)")


if __name__ == "__main__":
    main()
