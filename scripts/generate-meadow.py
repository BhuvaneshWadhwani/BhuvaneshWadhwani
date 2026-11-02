#!/usr/bin/env python3
"""Build an animated, dark-fantasy pixel-art GitHub contribution meadow.

Reads the contribution calendar from GitHub GraphQL and writes:
    dist/contribution-meadow.svg

Uses only Python's standard library. Set GITHUB_TOKEN in the environment.
"""
from __future__ import annotations

import json
import os
import random
import sys
import urllib.request
from datetime import date, datetime, timedelta, timezone
from html import escape
from pathlib import Path

USERNAME = "BhuvaneshWadhwani"
OUTPUT = Path("dist/contribution-meadow.svg")
WIDTH, HEIGHT = 1200, 500
RNG = random.Random(8142)

# Each level has a shadow, main face and moss/highlight colour.
LEVELS = {
    0: ("#18231f", "#26332b", "#344536"),
    1: ("#24402b", "#3d6039", "#66804a"),
    2: ("#355d32", "#62863d", "#9bad55"),
    3: ("#527a38", "#91a94a", "#c3c875"),
    4: ("#819b48", "#c0c96b", "#e8df9a"),
}
LEVEL_ENUM = {
    "NONE": 0, "FIRST_QUARTILE": 1, "SECOND_QUARTILE": 2,
    "THIRD_QUARTILE": 3, "FOURTH_QUARTILE": 4,
}


def fetch_calendar():
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        raise RuntimeError("GITHUB_TOKEN is not set.")

    end = date.today()
    start = end - timedelta(days=364)
    query = """
    query($login: String!, $from: DateTime!, $to: DateTime!) {
      user(login: $login) {
        contributionsCollection(from: $from, to: $to) {
          contributionCalendar {
            totalContributions
            weeks {
              contributionDays {
                date contributionCount contributionLevel
              }
            }
          }
        }
      }
    }"""
    payload = {
        "query": query,
        "variables": {
            "login": USERNAME,
            "from": datetime.combine(start, datetime.min.time(), timezone.utc).isoformat(),
            "to": datetime.combine(end, datetime.max.time(), timezone.utc).isoformat(),
        },
    }
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps(payload).encode(),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "pixel-meadow",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as response:
        result = json.loads(response.read().decode())

    if result.get("errors"):
        raise RuntimeError(json.dumps(result["errors"], indent=2))
    user = result.get("data", {}).get("user")
    if not user:
        raise RuntimeError(f"GitHub user {USERNAME!r} was not found.")

    cal = user["contributionsCollection"]["contributionCalendar"]
    days = []
    for week in cal["weeks"]:
        for day in week["contributionDays"]:
            days.append({
                "date": day["date"],
                "count": int(day["contributionCount"]),
                "level": LEVEL_ENUM.get(day["contributionLevel"], 0),
            })
    return days, int(cal["totalContributions"])


def rect(x, y, w, h, colour, extra=""):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{colour}" {extra}/>'


def poly(points, colour, extra=""):
    pts = " ".join(f"{x:.1f},{y:.1f}" for x, y in points)
    return f'<polygon points="{pts}" fill="{colour}" {extra}/>'


def label(x, y, value, size=10, colour="#9aa895", extra=""):
    return (f'<text x="{x}" y="{y}" font-family="monospace" font-size="{size}" '
            f'fill="{colour}" {extra}>{escape(str(value))}</text>')


def tree(x, base, scale=1.0, shade="#101a19", moss="#263d2b"):
    """Layered, blocky fir silhouette with a few pixel highlights."""
    s = scale
    parts = [rect(x + 9*s, base - 12*s, 5*s, 14*s, "#302b25")]
    tiers = [(base-22*s, 8), (base-34*s, 11), (base-48*s, 14), (base-62*s, 17)]
    for yy, half in tiers:
        parts.append(poly([(x+(12-half)*s, yy), (x+12*s, yy-15*s),
                           (x+(12+half)*s, yy)], shade))
        parts.append(poly([(x+(12-half+3)*s, yy-2*s), (x+12*s, yy-12*s),
                           (x+(12+half-4)*s, yy-2*s)], moss))
        parts.append(rect(x + (8 + RNG.randrange(0, 8))*s, yy-7*s, 2*s, 2*s, "#526343"))
    return "".join(parts)


def cat_sprite():
    """Small custom pixel-art orange explorer cat with cloak, pack and lantern."""
    p = []
    # Tail
    p += [rect(1, 29, 5, 5, "#bd682e"), rect(-3, 24, 5, 5, "#db8739"),
          rect(-2, 19, 4, 5, "#e7a34c")]
    # Back legs and body
    p += [rect(12, 31, 9, 13, "#9e542d"), rect(33, 31, 9, 13, "#9e542d"),
          rect(10, 23, 34, 17, "#c97832"), rect(15, 26, 20, 10, "#e49a47")]
    # Hood/head, ears, muzzle
    p += [rect(34, 5, 22, 22, "#d98137"), rect(35, 1, 8, 9, "#d98137"),
          rect(48, 1, 8, 9, "#d98137"), rect(37, 4, 4, 4, "#f0b18a"),
          rect(50, 4, 4, 4, "#f0b18a"), rect(37, 14, 5, 5, "#f3dfb9"),
          rect(49, 14, 5, 5, "#f3dfb9"), rect(39, 15, 2, 4, "#17201c"),
          rect(50, 15, 2, 4, "#17201c"), rect(44, 21, 5, 2, "#6d3d2a")]
    # Explorer cloak, pack, scarf and lantern
    p += [rect(13, 22, 24, 5, "#526047"), rect(18, 27, 18, 8, "#384638"),
          rect(12, 24, 8, 11, "#735039"), rect(13, 24, 7, 3, "#c3a16a"),
          rect(34, 25, 8, 4, "#c8b77d"), rect(40, 28, 4, 7, "#b69c61"),
          rect(5, 34, 6, 8, "#9e542d"), rect(4, 41, 9, 3, "#d28a42"),
          rect(32, 41, 10, 3, "#d28a42"),
          rect(45, 31, 4, 7, "#6e5838"), rect(44, 30, 6, 3, "#d9c17a"),
          rect(46, 32, 2, 3, "#ffe6a0")]
    # Pixel stripes
    p += [rect(18, 25, 4, 3, "#8e4b2b"), rect(27, 25, 4, 3, "#8e4b2b"),
          rect(42, 9, 3, 3, "#99512d")]
    return '<g class="cat">' + "".join(p) + '</g>'


def build_svg(days, total):
    # GraphQL calendar is Sunday-first, with possible partial weeks at either end.
    first = (date.fromisoformat(days[0]["date"]).weekday() + 1) % 7
    cells = [None] * first + days
    while len(cells) % 7:
        cells.append(None)
    weeks = len(cells) // 7

    # Fit the entire calendar naturally into the forest floor.
    cell_w, cell_h = 13, 12
    pitch_x, pitch_y = 17, 16
    grid_w = weeks * pitch_x
    grid_x = (WIDTH - grid_w - 6 * pitch_y) / 2
    grid_top = 305

    s = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}">',
        '<title>Enchanted forest GitHub contribution meadow</title>',
        '<desc>A dark fantasy pixel-art forest floor where mossy stone tiles form the GitHub contribution calendar, accompanied by an orange explorer cat.</desc>',
        '<defs>',
        '<linearGradient id="night" x1="0" y1="0" x2="0" y2="1"><stop stop-color="#080f1c"/><stop offset=".58" stop-color="#172532"/><stop offset="1" stop-color="#26352c"/></linearGradient>',
        '<linearGradient id="haze"><stop stop-color="#8ca89a" stop-opacity="0"/><stop offset=".5" stop-color="#9aaf9b" stop-opacity=".18"/><stop offset="1" stop-color="#8ca89a" stop-opacity="0"/></linearGradient>',
        '<radialGradient id="moonlight"><stop stop-color="#d8e1bd" stop-opacity=".25"/><stop offset="1" stop-color="#d8e1bd" stop-opacity="0"/></radialGradient>',
        '<filter id="glow" x="-100%" y="-100%" width="300%" height="300%"><feGaussianBlur stdDeviation="5"/></filter>',
        '</defs>',
        rect(0, 0, WIDTH, HEIGHT, "url(#night)"),
        '<circle cx="940" cy="83" r="100" fill="url(#moonlight)"/>',
        '<circle cx="940" cy="83" r="35" fill="#d9e1c3" opacity=".78"/>',
        '<circle cx="953" cy="72" r="32" fill="#172532"/>',
    ]

    # Star field
    for _ in range(100):
        x, y = RNG.randrange(10, WIDTH-10), RNG.randrange(8, 190)
        size = RNG.choice((1, 1, 2, 3))
        s.append(rect(x, y, size, size, RNG.choice(("#8ca39a", "#d1d8b5", "#6c8c89")),
                      f'opacity="{RNG.uniform(.25,.7):.2f}"'))

    # Distant ridges, towers and layered woodland
    s.append('<path d="M0 220 L120 145 210 190 315 126 430 205 555 143 680 204 800 140 910 195 1040 127 1200 190 V340 H0Z" fill="#12201f"/>')
    s.append('<path d="M0 245 L130 190 240 226 360 174 470 230 610 174 740 225 860 176 990 225 1110 170 1200 208 V355 H0Z" fill="#1b2b28"/>')
    # Ruined keep and broken arch
    s.append('<path d="M710 218 V138 L728 138 V111 L744 111 V138 H760 V218Z" fill="#101a20"/>')
    s.append('<path d="M704 140 L736 105 767 140Z" fill="#101a20"/>')
    s.append('<path d="M1010 258 V205 Q1010 160 1055 160 Q1100 160 1100 205 V258 H1083 V205 Q1083 177 1055 177 Q1027 177 1027 205 V258Z" fill="#24332e"/>')
    s.append(rect(0, 235, WIDTH, 42, "url(#haze)"))
    for x in range(-20, WIDTH+20, 48):
        s.append(tree(x, 300 + RNG.randrange(-8, 9), RNG.choice((.9, 1.0, 1.1)),
                      RNG.choice(("#0b1516", "#101d1b", "#14231e")),
                      RNG.choice(("#1d3328", "#263d2c", "#304632"))))

    # Ground: uneven forest floor, no panel or separate calendar card.
    s.append('<path d="M0 280 Q180 255 350 283 T700 277 T1000 281 T1200 270 V500 H0Z" fill="#17251e"/>')
    s.append('<path d="M0 330 Q210 298 410 329 T820 323 T1200 332 V500 H0Z" fill="#1d2d22"/>')
    s.append('<path d="M0 455 Q200 420 420 448 T850 445 T1200 452 V500 H0Z" fill="#0d1714"/>')

    # Calendar cells are stones embedded directly in the ground. Rows recede
    # slightly in size and shift sideways, creating a shallow ground perspective.
    for idx, item in enumerate(cells):
        if item is None:
            continue
        col, row = divmod(idx, 7)
        depth = row / 6
        x = grid_x + col * pitch_x + row * 3.0
        y = grid_top + row * pitch_y
        w = cell_w - row * .35
        h = cell_h - row * .25
        shadow, face, moss = LEVELS[item["level"]]
        # stone shadow and irregular lower edge
        s.append(poly([(x-1, y+3), (x+w+2, y+3), (x+w+1, y+h+4), (x+1, y+h+4)],
                      "#080f0d"))
        # top surface, slight perspective skew
        s.append(poly([(x, y), (x+w, y-1), (x+w+1, y+h), (x+1, y+h+1)],
                      shadow, 'stroke="#0c1712" stroke-width="1"'))
        s.append(poly([(x+1, y+1), (x+w-1, y), (x+w, y+h-2), (x+2, y+h-1)],
                      face))
        # Moss edging and a few small pixel clusters.
        if item["level"]:
            s.append(rect(x+2, y+2, max(2, w*.35), 2, moss))
            s.append(rect(x+w-4, y+h-4, 2, 2, moss))
            if item["level"] >= 3:
                s.append(rect(x+4, y+4, 2, 2, "#d8dc8b"))
        else:
            s.append(rect(x+3, y+3, 2, 2, "#405044", 'opacity=".65"'))
        s.append(f'<title>{escape(item["date"])}: {item["count"]} contributions</title>')

    # Ferns, grass, rocks and fungi around the calendar, not over it.
    for _ in range(105):
        x = RNG.randrange(8, WIDTH-8)
        y = RNG.choice((RNG.randrange(280, 300), RNG.randrange(438, 488)))
        colour = RNG.choice(("#304a31", "#405b37", "#607348", "#263d2d"))
        s.append(rect(x, y, 2, RNG.randrange(3, 9), colour))
        if RNG.random() < .35:
            s.append(rect(x+2, y+2, 3, 2, colour))
    for x, y, c in ((45, 405, "#8152a0"), (90, 427, "#9a5ca6"),
                    (1090, 405, "#4d8c91"), (1135, 430, "#6d9c89")):
        s += [rect(x, y+7, 5, 8, "#d0c7a5"), rect(x-3, y+3, 11, 5, c),
              rect(x, y, 5, 3, c), rect(x+1, y+4, 2, 2, "#d9c28b")]

    # A few foreground rocks frame the scene.
    for x, y, w in ((18, 460, 70), (210, 474, 52), (875, 472, 65), (1080, 460, 90)):
        s.append(poly([(x, y+12), (x+10, y), (x+w-8, y+2), (x+w, y+15), (x+w-6, y+27), (x+5, y+25)],
                      "#26332d", 'stroke="#3b4938" stroke-width="2"'))
        s.append(rect(x+15, y+7, 10, 2, "#536047"))

    # Cat walks along the upper edge of the embedded calendar.
    s.append('<g class="traveller"><animateTransform attributeName="transform" type="translate" values="80 0; 820 0; 80 0" dur="34s" repeatCount="indefinite"/>')
    s.append(f'<g transform="translate(0 245)">{cat_sprite()}</g></g>')
    s.append('<style><![CDATA[.cat{transform-origin:18px 30px;animation:tail 1.4s ease-in-out infinite}@keyframes tail{0%,100%{translate:0 0}50%{translate:0 -1px}}]]></style>')

    # Header and quiet legend, placed in the sky.
    s.append(label(34, 39, "FIELD NOTES  /  THE ENCHANTED WOOD", 10, "#9eae9a", 'letter-spacing="2"'))
    s.append(label(34, 65, "A YEAR IN THE WILDS", 21, "#dce2c5", 'font-weight="bold" letter-spacing="1"'))
    s.append(label(34, 86, f"{total:,} contributions gathered along the way", 10, "#93a18f"))
    s.append(label(34, 118, "LESS", 8, "#8d9a88"))
    for level in range(5):
        shadow, face, moss = LEVELS[level]
        x = 73 + level * 18
        s.append(rect(x, 108, 13, 12, shadow, 'stroke="#080f0d" stroke-width="1"'))
        s.append(rect(x+2, 110, 8, 3, face))
        if level:
            s.append(rect(x+3, 114, 3, 2, moss))
    s.append(label(172, 118, "MORE", 8, "#8d9a88"))
    # Small month labels, positioned above first week of each month.
    seen = set()
    for i, item in enumerate(cells):
        if item and date.fromisoformat(item["date"]).day <= 7:
            month = date.fromisoformat(item["date"]).strftime("%b").upper()
            col = i // 7
            if month not in seen:
                seen.add(month)
                x = grid_x + col*pitch_x
                s.append(label(x, grid_top-12, month, 8, "#8e9e8b"))

    # Tiny drifting fireflies.
    for i in range(13):
        x, y = RNG.randrange(40, WIDTH-40), RNG.randrange(210, 430)
        s.append(f'<circle cx="{x}" cy="{y}" r="1.8" fill="#e2d58b"><animate attributeName="opacity" values=".12;.85;.12" dur="{RNG.randrange(3,7)}s" begin="{RNG.randrange(0,5)}s" repeatCount="indefinite"/></circle>')
    s.append(label(34, 482, "KEEP WANDERING.", 8, "#718473", 'letter-spacing="2"'))
    s.append('</svg>')
    return "\n".join(s)


def main():
    days, total = fetch_calendar()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(build_svg(days, total), encoding="utf-8")
    print(f"Wrote {OUTPUT} ({len(days)} days, {total} contributions).")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
