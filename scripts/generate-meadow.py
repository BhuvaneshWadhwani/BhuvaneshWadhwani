#!/usr/bin/env python3
"""Generate a dark-fantasy, high-detail pixel-art GitHub contribution meadow.

Required environment:
  GITHUB_TOKEN: token with permission to read the user's public contribution data.

The script writes dist/contribution-meadow.svg.
"""
from __future__ import annotations

import json
import os
import random
import sys
import urllib.error
import urllib.request
from datetime import date, datetime, timedelta, timezone
from html import escape
from pathlib import Path

USERNAME = "BhuvaneshWadhwani"
OUTPUT = Path("dist/contribution-meadow.svg")
API_URL = "https://api.github.com/graphql"
WIDTH, HEIGHT = 1200, 470
CELL = 15
GAP = 4
STEP = CELL + GAP
GRID_X = 112
GRID_Y = 190
RNG = random.Random(29)

LEVEL_COLOURS = {
    0: ("#17231f", "#26352d", "#34483a"),
    1: ("#29452f", "#42683a", "#648449"),
    2: ("#426b39", "#6e9345", "#9db75a"),
    3: ("#709847", "#a7bd58", "#d0d77a"),
    4: ("#b1c968", "#e2e39a", "#fff0bd"),
}
LEVEL_NAMES = {
    0: "No contributions",
    1: "Low contributions",
    2: "Medium contributions",
    3: "High contributions",
    4: "Very high contributions",
}


def github_contributions() -> dict:
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        raise RuntimeError("GITHUB_TOKEN environment variable is missing.")

    today = date.today()
    start = today - timedelta(days=364)
    query = """
    query($login: String!, $from: DateTime!, $to: DateTime!) {
      user(login: $login) {
        contributionsCollection(from: $from, to: $to) {
          contributionCalendar {
            totalContributions
            weeks {
              contributionDays {
                date
                contributionCount
                contributionLevel
              }
            }
          }
        }
      }
    }
    """
    payload = {
        "query": query,
        "variables": {
            "login": USERNAME,
            "from": datetime.combine(start, datetime.min.time(), timezone.utc).isoformat(),
            "to": datetime.combine(today, datetime.max.time(), timezone.utc).isoformat(),
        },
    }
    request = urllib.request.Request(
        API_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "contribution-meadow-generator",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            result = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"GitHub API returned HTTP {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Could not reach GitHub GraphQL API: {exc}") from exc

    if result.get("errors"):
        raise RuntimeError("GitHub GraphQL error: " + json.dumps(result["errors"]))
    user = result.get("data", {}).get("user")
    if not user:
        raise RuntimeError(f"GitHub user {USERNAME!r} was not found or is inaccessible.")

    calendar = user["contributionsCollection"]["contributionCalendar"]
    days = []
    for week in calendar["weeks"]:
        for item in week["contributionDays"]:
            level_name = item["contributionLevel"]
            level = {
                "NONE": 0,
                "FIRST_QUARTILE": 1,
                "SECOND_QUARTILE": 2,
                "THIRD_QUARTILE": 3,
                "FOURTH_QUARTILE": 4,
            }.get(level_name, 0)
            days.append({
                "date": item["date"],
                "count": int(item["contributionCount"]),
                "level": level,
            })
    return {"days": days, "total": int(calendar["totalContributions"])}


def rect(x, y, w, h, fill, extra=""):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}" {extra}/>'


def pixel(x, y, colour, size=3):
    return rect(x, y, size, size, colour)


def text(x, y, value, size=11, fill="#aeb9a4", extra=""):
    return (
        f'<text x="{x}" y="{y}" font-family="monospace" font-size="{size}" '
        f'fill="{fill}" {extra}>{escape(str(value))}</text>'
    )


def draw_tree(x, ground, scale=1.0, tint="#101b19", highlight="#24382d"):
    """Small blocky fir tree built from pixel-like rectangles."""
    s = scale
    out = [rect(x + 7*s, ground - 13*s, 5*s, 14*s, "#302a24")]
    for row, half in enumerate((3, 5, 7, 9)):
        yy = ground - (18 + row*7)*s
        xx = x + (12-half)*s
        out.append(rect(xx, yy, half*2*s, 6*s, tint))
        out.append(rect(xx + 2*s, yy + 2*s, max(2, half-1)*s, 2*s, highlight))
    out.append(pixel(x + 4*s, ground - 29*s, "#344a35", 2*s))
    return "".join(out)


def draw_cat(x, y):
    """Pixel sprite: orange explorer cat with a tiny satchel and scarf."""
    p = []
    # Tail, animated separately.
    p.append('<g class="tail" transform-origin="8px 34px">')
    p += [rect(0, 30, 4, 4, "#d77b32"), rect(-3, 26, 4, 4, "#e99a45"),
          rect(-3, 22, 4, 4, "#f0b45f"), rect(-7, 20, 4, 4, "#d77b32")]
    p.append('</g>')
    # Body and legs.
    p += [rect(10, 25, 29, 14, "#d77b32"), rect(14, 28, 20, 8, "#f0a34d"),
          rect(12, 37, 7, 8, "#c96b2b"), rect(31, 37, 7, 8, "#c96b2b"),
          rect(11, 43, 9, 3, "#eaa04b"), rect(30, 43, 9, 3, "#eaa04b")]
    # Head, ears and face.
    p += [rect(31, 8, 20, 19, "#e58b38"), rect(32, 4, 7, 8, "#e58b38"),
          rect(44, 4, 7, 8, "#e58b38"), rect(34, 7, 3, 4, "#f3b4a0"),
          rect(46, 7, 3, 4, "#f3b4a0"), rect(34, 15, 4, 4, "#f3e6bd"),
          rect(45, 15, 4, 4, "#f3e6bd"), rect(35, 16, 2, 3, "#17211d"),
          rect(46, 16, 2, 3, "#17211d"), rect(40, 21, 4, 2, "#70402c")]
    # Stripes, chest, scarf, satchel.
    p += [rect(17, 26, 4, 3, "#8f4b2b"), rect(25, 25, 4, 3, "#8f4b2b"),
          rect(39, 11, 3, 3, "#9c542e"), rect(37, 27, 10, 4, "#d6c17e"),
          rect(45, 28, 4, 8, "#c7ad68"), rect(9, 29, 6, 8, "#8a5839"),
          rect(8, 30, 7, 2, "#d8bd7a")]
    # Backpack strap and small lantern.
    p += [rect(20, 24, 3, 12, "#6b4934"), rect(23, 31, 4, 5, "#c3a66b"),
          rect(24, 32, 2, 3, "#ffe49a")]
    return f'<g transform="translate({x} {y})">' + "".join(p) + '</g>'


def make_svg(data):
    days = data["days"]
    # Pad to complete Sunday-to-Saturday columns as GitHub's calendar does.
    if not days:
        raise RuntimeError("GitHub returned an empty contribution calendar.")
    first_weekday = date.fromisoformat(days[0]["date"]).weekday()
    # GitHub's calendar starts Sunday; Python Monday=0.
    leading = (first_weekday + 1) % 7
    cells = [None] * leading + days
    while len(cells) % 7:
        cells.append(None)
    weeks = len(cells) // 7

    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}">',
        '<title>Dark fantasy pixel-art GitHub contribution meadow</title>',
        '<desc>A moonlit forest ruin with a glowing contribution calendar and an orange explorer cat.</desc>',
        '<defs>',
        '<linearGradient id="sky" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#080e18"/><stop offset=".62" stop-color="#111d25"/><stop offset="1" stop-color="#1c2b27"/></linearGradient>',
        '<linearGradient id="mist" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#9bb89a" stop-opacity="0"/><stop offset=".5" stop-color="#9bb89a" stop-opacity=".16"/><stop offset="1" stop-color="#9bb89a" stop-opacity="0"/></linearGradient>',
        '<radialGradient id="moonGlow"><stop offset="0" stop-color="#dce7bd" stop-opacity=".25"/><stop offset="1" stop-color="#dce7bd" stop-opacity="0"/></radialGradient>',
        '<filter id="softGlow" x="-80%" y="-80%" width="260%" height="260%"><feGaussianBlur stdDeviation="4"/></filter>',
        '<filter id="tileGlow" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="2"/></filter>',
        '</defs>',
        rect(0, 0, WIDTH, HEIGHT, "url(#sky)"),
        # Moon and distant atmosphere.
        '<circle cx="1000" cy="76" r="75" fill="url(#moonGlow)"/>',
        '<circle cx="1000" cy="76" r="27" fill="#d7dfbd" opacity=".82"/>',
        '<circle cx="1010" cy="67" r="25" fill="#111d25"/>',
    ]

    # Stars: restrained, crisp pixels rather than scattered stock-art sparkles.
    for i in range(95):
        x = RNG.randint(20, WIDTH - 20)
        y = RNG.randint(15, 150)
        s = RNG.choice([1, 2, 2, 3])
        c = RNG.choice(["#839a8a", "#b7c59a", "#607c79"])
        out.append(rect(x, y, s, s, c, f'opacity="{RNG.uniform(.25,.75):.2f}"'))

    # Distant mountain / forest silhouettes.
    out.append('<path d="M0 165 L95 118 L165 151 L250 105 L335 157 L420 116 L505 158 L610 110 L700 160 L805 116 L900 156 L1000 112 L1100 159 L1200 120 L1200 280 L0 280Z" fill="#14231f"/>')
    out.append('<path d="M0 188 L120 148 L215 183 L330 140 L440 185 L560 145 L680 188 L790 151 L910 185 L1030 146 L1140 181 L1200 162 L1200 300 L0 300Z" fill="#1a2d25"/>')
    out.append(rect(0, 168, WIDTH, 34, "url(#mist)"))
    # Ancient broken tower silhouette.
    out.append('<path d="M870 185 L870 131 L880 131 L880 119 L890 119 L890 131 L900 131 L900 185Z" fill="#101a1c"/>')
    out.append('<path d="M866 132 L885 113 L904 132Z" fill="#101a1c"/>')
    out.append(rect(883, 146, 4, 9, "#a8b68a", 'opacity=".45"'))

    # Forest wall.
    for x in range(-20, WIDTH + 20, 54):
        out.append(draw_tree(x, 246 + RNG.randint(-5, 8), RNG.choice([1.0, 1.15, 1.3]),
                             RNG.choice(["#0e1918", "#12201c", "#17271e"]),
                             RNG.choice(["#20372a", "#29402d", "#304932"])))

    # Calendar frame: dark carved-stone panel.
    grid_width = weeks * STEP - GAP
    panel_x, panel_y = 87, 157
    panel_w, panel_h = grid_width + 58, 190
    out.append(rect(panel_x, panel_y, panel_w, panel_h, "#0b1516", 'rx="5" stroke="#52634a" stroke-width="2"'))
    out.append(rect(panel_x + 5, panel_y + 5, panel_w - 10, panel_h - 10, "#101d1b", 'rx="3" stroke="#263d30" stroke-width="1"'))
    # Tiny stone rivets.
    for xx in (panel_x + 10, panel_x + panel_w - 14):
        for yy in (panel_y + 10, panel_y + panel_h - 14):
            out.append(rect(xx, yy, 4, 4, "#718064"))

    # Heading.
    out.append(text(30, 35, "THE CHRONICLES OF", 10, "#91a18b", 'letter-spacing="3"'))
    out.append(text(30, 61, "A YEAR IN THE WILDS", 21, "#d7dfc0", 'font-weight="bold" letter-spacing="1"'))
    out.append(text(30, 82, "A record of work, patience and small victories", 10, "#829184"))
    out.append(text(30, 111, "CONTRIBUTION FIELD", 9, "#a9b894", 'letter-spacing="2"'))

    # Month labels from actual dates.
    month_positions = {}
    for index, item in enumerate(cells):
        if item and date.fromisoformat(item["date"]).day <= 7:
            col = index // 7
            month_positions.setdefault(date.fromisoformat(item["date"]).strftime("%b").upper(), col)
    for month, col in month_positions.items():
        out.append(text(GRID_X + col * STEP, 178, month, 8, "#94a28b"))

    # Weekday labels.
    for row, label in enumerate(("S", "", "T", "", "T", "", "S")):
        if label:
            out.append(text(97, GRID_Y + row * STEP + 10, label, 8, "#748678"))

    # Contribution tiles: inset bevels, random moss speckle, level glow.
    for index, item in enumerate(cells):
        if item is None:
            continue
        col, row = divmod(index, 7)
        x = GRID_X + col * STEP
        y = GRID_Y + row * STEP
        level = item["level"]
        dark, mid, light = LEVEL_COLOURS[level]
        if level:
            out.append(rect(x - 2, y - 2, CELL + 4, CELL + 4, light,
                            f'opacity="{0.12 + level*0.045:.2f}" rx="2" filter="url(#tileGlow)"'))
        out.append(rect(x, y, CELL, CELL, dark, 'rx="1" stroke="#07100f" stroke-width="1"'))
        out.append(rect(x + 2, y + 2, CELL - 4, 3, mid))
        out.append(rect(x + 2, y + 5, 3, CELL - 7, mid, 'opacity=".72"'))
        out.append(rect(x + 5, y + 5, CELL - 7, CELL - 7, dark))
        # Tiny pixel highlights make each tile feel like textured moss/stone.
        if level:
            out.append(rect(x + 4, y + 5, 2, 2, light, 'opacity=".9"'))
            out.append(rect(x + 9, y + 9, 2, 2, mid, 'opacity=".85"'))
            if level >= 3:
                out.append(rect(x + 11, y + 3, 2, 2, light))
        else:
            out.append(rect(x + 10, y + 10, 2, 2, "#405047", 'opacity=".5"'))
        out.append(
            f'<title>{escape(item["date"])}: {item["count"]} contributions ({LEVEL_NAMES[level]})</title>'
        )

    # Bottom border and legend.
    legend_y = panel_y + panel_h - 17
    out.append(text(panel_x + 12, legend_y + 7, f'{data["total"]} CONTRIBUTIONS', 8, "#b7c39e"))
    out.append(text(panel_x + panel_w - 170, legend_y + 7, "LESS", 7, "#879587"))
    for i in range(5):
        dark, mid, light = LEVEL_COLOURS[i]
        lx = panel_x + panel_w - 137 + i * 16
        out.append(rect(lx, legend_y - 3, 11, 11, dark, 'stroke="#65765a" stroke-width=".6"'))
        out.append(rect(lx + 2, legend_y - 1, 7, 3, mid))
        if i:
            out.append(rect(lx + 3, legend_y + 3, 2, 2, light))
    out.append(text(panel_x + panel_w - 48, legend_y + 7, "MORE", 7, "#b7c39e"))

    # Foreground ground plane and path.
    out.append('<path d="M0 354 Q180 326 340 352 T670 349 T960 345 T1200 355 L1200 470 L0 470Z" fill="#0a1412"/>')
    out.append('<path d="M0 383 Q230 350 450 379 T900 375 T1200 390" fill="none" stroke="#263c2c" stroke-width="3"/>')
    # Broken stepping-stone trail.
    for i, (x, y) in enumerate([(500, 403), (555, 391), (612, 405), (674, 390), (733, 402), (792, 390)]):
        out.append(rect(x, y, 24, 7, "#25332b", 'rx="2"'))
        out.append(rect(x + 3, y + 1, 9, 2, "#435342"))
    # Foreground trees framing the scene.
    out.append(draw_tree(-3, 435, 2.2, "#08110f", "#1b3023"))
    out.append(draw_tree(1090, 438, 2.5, "#08110f", "#1b3023"))
    out.append(draw_tree(1150, 438, 1.7, "#0a1512", "#203626"))

    # Grass tufts and tiny mushrooms, deliberately sparse.
    for i in range(70):
        x = RNG.randint(15, WIDTH - 15)
        y = RNG.randint(355, 460)
        c = RNG.choice(["#263f2c", "#365334", "#526a3b"])
        out.append(rect(x, y, 2, RNG.randint(4, 10), c))
        if i % 5 == 0:
            out.append(rect(x + 2, y + 2, 3, 2, c))
    for x, y in [(80, 405), (1030, 412), (930, 438), (300, 430)]:
        out.append(rect(x, y + 5, 5, 7, "#d8d0ad"))
        out.append(rect(x - 2, y + 2, 9, 4, "#8d5548"))
        out.append(rect(x, y, 5, 3, "#b36b52"))

    # Lantern posts and fireflies.
    out.append(rect(64, 337, 4, 30, "#514532"))
    out.append(rect(58, 331, 16, 9, "#6d6242", 'rx="2"'))
    out.append(rect(62, 333, 8, 5, "#e6c77d", 'opacity=".8"'))
    out.append('<circle cx="66" cy="337" r="22" fill="#d7b96c" opacity=".13" filter="url(#softGlow)"/>')
    for i in range(12):
        x = RNG.randint(90, 1110)
        y = RNG.randint(300, 430)
        out.append(f'<circle cx="{x}" cy="{y}" r="1.5" fill="#d5d98a" opacity=".8"><animate attributeName="opacity" values=".15;.9;.15" dur="{RNG.randint(2,5)}s" repeatCount="indefinite" begin="{RNG.randint(0,4)}s"/></circle>')

    # Cat walks along the foreground path. Moderate pace; bob and tail movement.
    out.append('<g class="walker">')
    out.append('<animateTransform attributeName="transform" type="translate" values="145 0; 875 0; 145 0" dur="30s" repeatCount="indefinite"/>')
    out.append('<animate attributeName="opacity" values="1;1;1" dur="30s" repeatCount="indefinite"/>')
    out.append(draw_cat(0, 354))
    out.append('</g>')
    out.append('<style><![CDATA['
               '.walker{animation:walk 30s linear infinite;transform-box:fill-box;}'
               '.tail{animation:tail 1.6s ease-in-out infinite;transform-box:fill-box;}'
               '@keyframes tail{0%,100%{transform:rotate(-8deg)}50%{transform:rotate(16deg)}}'
               ']]></style>')

    # Footer ornament.
    out.append(text(30, 454, "KEEP WANDERING.", 8, "#7f917f", 'letter-spacing="2"'))
    out.append(text(1170, 454, "✦", 12, "#a9b88a", 'text-anchor="end"'))
    out.append('</svg>')
    return "\n".join(out)


def main():
    data = github_contributions()
    svg = make_svg(data)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(svg, encoding="utf-8")
    print(f"Generated {OUTPUT} with {len(data['days'])} days and {data['total']} contributions.")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
