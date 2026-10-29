#!/usr/bin/env python3
"""Genera stats.svg: estadísticas, lenguajes y rachas, directo desde la API de GitHub.
Sin dependencias externas (solo stdlib)."""
import datetime as dt
import json
import os
import sys
import urllib.request
from html import escape

USER = os.environ.get("GH_USER", "vicente-arriagada-lost")
TOKEN = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
OUT = os.environ.get("OUT", "stats.svg")

GREEN, CYAN, MAGENTA, TEXT, DIM = "#00ff41", "#00f0ff", "#ff00e5", "#c9d1d9", "#8b949e"
FALLBACK = ["#00f0ff", "#ff00e5", "#ffe600", "#39ff14", "#7c4dff", "#ff7a00", "#8b949e", "#58a6ff"]


def gql(query):
    if not TOKEN:
        sys.exit("Falta GH_TOKEN o GITHUB_TOKEN")
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": query}).encode(),
        headers={"Authorization": f"bearer {TOKEN}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        data = json.load(r)
    if "errors" in data:
        sys.exit(f"Error GraphQL: {data['errors']}")
    return data["data"]


def collect():
    today = dt.date.today()

    base = gql(f"""{{ user(login:"{USER}") {{
        createdAt
        repositoriesContributedTo(first:1, contributionTypes:[COMMIT,ISSUE,PULL_REQUEST,REPOSITORY]){{totalCount}}
        repositories(first:100, ownerAffiliations:OWNER, isFork:false){{nodes{{
            stargazerCount
            languages(first:10, orderBy:{{field:SIZE, direction:DESC}}){{edges{{size node{{name color}}}}}}
        }}}}
    }} }}""")["user"]

    first_year = int(base["createdAt"][:4])
    years = range(first_year, today.year + 1)
    body = "\n".join(f"""y{y}: contributionsCollection(from:"{y}-01-01T00:00:00Z", to:"{y}-12-31T23:59:59Z"){{
        totalCommitContributions restrictedContributionsCount
        totalPullRequestContributions totalIssueContributions
        contributionCalendar{{totalContributions weeks{{contributionDays{{date contributionCount}}}}}}
    }}""" for y in years)
    cols = gql(f'{{ user(login:"{USER}") {{ {body} }} }}')["user"]

    commits = prs = issues = 0
    days = {}
    for y in years:
        c = cols[f"y{y}"]
        commits += c["totalCommitContributions"] + c["restrictedContributionsCount"]
        prs += c["totalPullRequestContributions"]
        issues += c["totalIssueContributions"]
        for w in c["contributionCalendar"]["weeks"]:
            for d in w["contributionDays"]:
                days[d["date"]] = d["contributionCount"]

    stars = sum(r["stargazerCount"] for r in base["repositories"]["nodes"])
    langs = {}
    for r in base["repositories"]["nodes"]:
        for e in r["languages"]["edges"]:
            n = e["node"]["name"]
            cur = langs.setdefault(n, {"size": 0, "color": e["node"]["color"]})
            cur["size"] += e["size"]

    return {
        "stars": stars, "commits": commits, "prs": prs, "issues": issues,
        "contributed": base["repositoriesContributedTo"]["totalCount"],
        "langs": langs, "days": days, "today": today,
    }


def streaks(days, today):
    dates = sorted(dt.date.fromisoformat(d) for d, c in days.items() if dt.date.fromisoformat(d) <= today)
    active = {d for d in dates if days[d.isoformat()] > 0}
    total = sum(days[d.isoformat()] for d in dates)
    first = min(active) if active else today

    longest, l_start, l_end = 0, None, None
    run, run_start = 0, None
    for d in dates:
        if d in active:
            if run == 0:
                run_start = d
            run += 1
            if run > longest:
                longest, l_start, l_end = run, run_start, d
        else:
            run = 0

    # racha actual: termina hoy, o ayer si hoy aún no hay actividad
    end = today if today in active else today - dt.timedelta(days=1)
    cur, c_end = 0, end
    d = end
    while d in active:
        cur += 1
        d -= dt.timedelta(days=1)
    c_start = end - dt.timedelta(days=cur - 1) if cur else None
    return total, first, cur, c_start, c_end if cur else None, longest, l_start, l_end


def fmt(d):
    return f"{d:%b} {d.day}"


def fmt_range(a, b):
    if a is None:
        return "—"
    return fmt(a) if a == b else f"{fmt(a)} - {fmt(b)}"


def render(d):
    total, first, cur, c_s, c_e, longest, l_s, l_e = streaks(d["days"], d["today"])

    # lenguajes: top 8 en %
    tot_size = sum(v["size"] for v in d["langs"].values()) or 1
    top = sorted(d["langs"].items(), key=lambda kv: -kv[1]["size"])[:8]
    bar, legend, x = [], [], 0.0
    bar_w = 492
    for k, (name, v) in enumerate(top):
        pct = v["size"] / tot_size * 100
        color = v["color"] or FALLBACK[k % len(FALLBACK)]
        w = pct / 100 * bar_w
        bar.append(f'<rect x="{384 + x:.1f}" y="52" width="{w:.1f}" height="10" fill="{color}"/>')
        x += w
        cx, cy = 384 + (k % 2) * 250, 94 + (k // 2) * 26
        legend.append(
            f'<circle cx="{cx + 5}" cy="{cy - 4}" r="5" fill="{color}"/>'
            f'<text x="{cx + 18}" y="{cy}" font-size="12" fill="{TEXT}">{escape(name)} <tspan fill="{DIM}">({pct:.2f}%)</tspan></text>'
        )

    rows = [("Total Stars", d["stars"]), ("Total Commits", d["commits"]), ("Total PRs", d["prs"]),
            ("Total Issues", d["issues"]), ("Contributed to", d["contributed"])]
    stat_rows = "".join(
        f'<text x="24" y="{76 + k * 26}" font-size="14" fill="{TEXT}" font-weight="600"><tspan fill="{CYAN}">▸</tspan> {label}</text>'
        f'<text x="250" y="{76 + k * 26}" font-size="14" fill="{CYAN}" font-weight="700">{val}</text>'
        for k, (label, val) in enumerate(rows)
    )

    R = 28
    C = 2 * 3.14159265 * R
    frac = min(1.0, cur / longest) if longest else 0
    offset = C * (1 - frac)

    first_s = f"{first:%b} {first.day}, {first.year}"
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 900 360" width="100%" role="img" aria-label="GitHub stats for {escape(USER)}">
<style>
text{{font-family:'Segoe UI',Ubuntu,'Helvetica Neue',Arial,sans-serif}}
.ring{{stroke-dasharray:{C:.1f};animation:draw 1.6s ease-out}}
@keyframes draw{{from{{stroke-dashoffset:{C:.1f}}}}}
@keyframes pulse{{0%,100%{{opacity:.55}}50%{{opacity:1}}}}
.glow{{animation:pulse 3s ease-in-out infinite}}
@media (prefers-reduced-motion:reduce){{.ring,.glow{{animation:none}}}}
</style>
<defs><clipPath id="barclip"><rect x="384" y="52" width="{bar_w}" height="10" rx="5"/></clipPath></defs>
<rect width="900" height="360" rx="10" fill="#0d1117"/>

<rect x=".5" y=".5" width="340" height="190" rx="8" fill="#0d1117" stroke="{GREEN}" stroke-opacity=".7"/>
<text x="24" y="34" font-size="18" font-weight="700" fill="{GREEN}">My GitHub Statistics</text>
{stat_rows}

<rect x="360.5" y=".5" width="539" height="190" rx="8" fill="#0d1117" stroke="{CYAN}" stroke-opacity=".7"/>
<text x="384" y="34" font-size="18" font-weight="700" fill="{GREEN}">My Programming Languages</text>
<g clip-path="url(#barclip)">{"".join(bar)}</g>
{"".join(legend)}

<rect x=".5" y="210.5" width="899" height="149" rx="8" fill="#0d1117" stroke="{GREEN}" stroke-opacity=".7"/>
<path d="M300 232V338M600 232V338" stroke="{GREEN}" stroke-opacity=".5"/>

<text x="150" y="270" font-size="32" font-weight="700" fill="{CYAN}" text-anchor="middle">{total}</text>
<text x="150" y="298" font-size="14" fill="{TEXT}" text-anchor="middle">Total Contributions</text>
<text x="150" y="320" font-size="12" fill="{DIM}" text-anchor="middle">{first_s} - Present</text>

<circle cx="450" cy="256" r="{R}" fill="none" stroke="{MAGENTA}" stroke-opacity=".2" stroke-width="5"/>
<circle class="ring glow" cx="450" cy="256" r="{R}" fill="none" stroke="{MAGENTA}" stroke-width="5" stroke-linecap="round" transform="rotate(-90 450 256)" style="stroke-dashoffset:{offset:.1f}"/>
<text x="450" y="263" font-size="22" font-weight="700" fill="{GREEN}" text-anchor="middle">{cur}</text>
<text x="450" y="308" font-size="14" font-weight="700" fill="{CYAN}" text-anchor="middle">Current Streak</text>
<text x="450" y="328" font-size="12" fill="{DIM}" text-anchor="middle">{fmt_range(c_s, c_e)}</text>

<text x="750" y="270" font-size="32" font-weight="700" fill="{CYAN}" text-anchor="middle">{longest}</text>
<text x="750" y="298" font-size="14" fill="{TEXT}" text-anchor="middle">Longest Streak</text>
<text x="750" y="320" font-size="12" fill="{DIM}" text-anchor="middle">{fmt_range(l_s, l_e)}</text>
</svg>
"""


def main():
    svg = render(collect())
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"OK -> {OUT}")


if __name__ == "__main__":
    main()
