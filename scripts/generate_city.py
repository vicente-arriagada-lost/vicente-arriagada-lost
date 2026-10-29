#!/usr/bin/env python3
"""Genera city.svg: una ciudad isométrica donde cada edificio es un día del año.
Más alto = más contribuciones. Sin dependencias externas (solo stdlib)."""
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

S = 9.0          # tamaño de cada tile
MAX_H = 46.0     # altura máxima de un edificio
BASE = "#2dd4bf" # color base (teal)
BG1, BG2 = "#0b2a2a", "#061617"

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


def shade(hex_color, f):
    r, g, b = (int(hex_color[i:i + 2], 16) for i in (1, 3, 5))
    return "#%02x%02x%02x" % tuple(min(255, int(c * f)) for c in (r, g, b))


def proj(i, j, z=0.0):
    return ((i - j) * S * 0.866, (i + j) * S * 0.5 - z)


def pts(points):
    return " ".join(f"{x:.1f},{y:.1f}" for x, y in points)


def main():
    cal = fetch()
    cells = []  # (i, j, count, date)
    for wi, week in enumerate(cal["weeks"]):
        for d in week["contributionDays"]:
            cells.append((wi, d["weekday"], d["contributionCount"], d["date"]))

    total = cal["totalContributions"]
    active = sum(1 for c in cells if c[2] > 0)
    busiest = max((c[2] for c in cells), default=0)
    n_weeks = len(cal["weeks"])

    # Geometría
    polys = []
    all_pts = []
    for i, j, c, date in sorted(cells, key=lambda c: (c[0] + c[1], c[0])):
        corners = [(i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1)]
        ground = [proj(*p) for p in corners]
        all_pts += ground
        if c == 0:
            polys.append(
                f'<polygon points="{pts(ground)}" fill="#0f3a3a" fill-opacity=".55" '
                f'stroke="#1b5555" stroke-width=".5"/>'
            )
            continue
        level = max(1, math.ceil(c / busiest * 4))
        h = 5 + (c / busiest) * (MAX_H - 5)
        col = shade(BASE, 0.45 + 0.14 * level)
        top = [proj(*p, h) for p in corners]
        all_pts += top
        a, b, cc, d = corners
        left = [proj(*d), proj(*cc), proj(*cc, h), proj(*d, h)]
        right = [proj(*b), proj(*cc), proj(*cc, h), proj(*b, h)]
        polys.append(
            f'<g><title>{date}: {c} contributions</title>'
            f'<polygon points="{pts(left)}" fill="{shade(col, .62)}"/>'
            f'<polygon points="{pts(right)}" fill="{shade(col, .8)}"/>'
            f'<polygon points="{pts(top)}" fill="{shade(col, 1.15)}"/></g>'
        )

    min_x = min(p[0] for p in all_pts) - 30
    max_x = max(p[0] for p in all_pts) + 30
    min_y = min(p[1] for p in all_pts) - 30
    max_y = max(p[1] for p in all_pts) + 30
    w, h = max_x - min_x, max_y - min_y

    mono = "ui-monospace,SFMono-Regular,Menlo,Consolas,monospace"
    tx, ty = min_x + 18, max_y - 62
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="{min_x:.0f} {min_y:.0f} {w:.0f} {h:.0f}" width="100%" role="img" aria-label="Contribution city {YEAR}: {total} contributions">
<defs><radialGradient id="bg" cx="50%" cy="45%" r="75%"><stop offset="0" stop-color="{BG1}"/><stop offset="1" stop-color="{BG2}"/></radialGradient></defs>
<rect x="{min_x:.0f}" y="{min_y:.0f}" width="{w:.0f}" height="{h:.0f}" rx="10" fill="url(#bg)"/>
{chr(10).join(polys)}
<g font-family="{mono}" fill="#5eead4">
<text x="{tx:.0f}" y="{ty - 34:.0f}" font-size="6" letter-spacing="2" fill="#2dd4bf" opacity=".8">CONTRIBUTION CITY {YEAR}</text>
<text x="{tx:.0f}" y="{ty - 8:.0f}" font-size="22" font-weight="700" fill="#e6fffb">{total}</text>
<text x="{tx:.0f}" y="{ty + 4:.0f}" font-size="6" fill="#99f6e4">contributions this year</text>
<text x="{tx:.0f}" y="{ty + 20:.0f}" font-size="6">{active} active days · busiest day: {busiest}</text>
<text x="{tx:.0f}" y="{ty + 34:.0f}" font-size="5" fill="#2dd4bf" opacity=".6">@{USER} · {n_weeks} weeks</text>
</g>
</svg>
"""
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"OK -> {OUT} ({total} contribuciones, {active} días activos, máx {busiest})")


if __name__ == "__main__":
    main()
