import os
import json
import random
import urllib.request
from datetime import date, datetime, timedelta
from pathlib import Path
from xml.sax.saxutils import escape

USERNAME = "BhuvaneshWadhwani"
TOKEN = os.environ["GITHUB_TOKEN"]

OUTPUT = Path("dist/contribution-meadow.svg")

# --------------------------------------------------
# 1. Retrieve GitHub contribution data
# --------------------------------------------------

today = date.today()
start_date = today - timedelta(days=364)

query = """
query($login: String!, $from: DateTime!, $to: DateTime!) {
  user(login: $login) {
    contributionsCollection(from: $from, to: $to) {
      contributionCalendar {
        weeks {
          contributionDays {
            date
            contributionCount
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
        "from": start_date.isoformat() + "T00:00:00Z",
        "to": today.isoformat() + "T23:59:59Z"
    }
}

request = urllib.request.Request(
    "https://api.github.com/graphql",
    data=json.dumps(payload).encode("utf-8"),
    headers={
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json",
        "User-Agent": "GitHub-Contribution-Meadow"
    }
)

with urllib.request.urlopen(request) as response:
    result = json.loads(response.read().decode("utf-8"))

if "errors" in result:
    raise RuntimeError(f"GitHub API error: {result['errors']}")

user_data = result["data"]["user"]

if user_data is None:
    raise RuntimeError(f"GitHub user not found: {USERNAME}")

weeks = user_data["contributionsCollection"]["contributionCalendar"]["weeks"]

# --------------------------------------------------
# 2. SVG layout
# --------------------------------------------------

WIDTH = 1160
HEIGHT = 330

CELL = 14
GAP = 4
STEP = CELL + GAP

X_START = 110
Y_START = 145

GRID_WIDTH = len(weeks) * STEP

# Contribution intensity colours
GRASS = [
    "#142C25",
    "#245437",
    "#397B3D",
    "#68A83C",
    "#B3D957"
]

# --------------------------------------------------
# 3. SVG helpers
# --------------------------------------------------

svg = []

def add(value):
    svg.append(value)

def rect(x, y, w, h, fill, radius=0):
    add(
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" '
        f'rx="{radius}" fill="{fill}"/>'
    )

# --------------------------------------------------
# 4. Background and night environment
# --------------------------------------------------

add(f"""
<svg xmlns="http://www.w3.org/2000/svg"
     width="{WIDTH}" height="{HEIGHT}"
     viewBox="0 0 {WIDTH} {HEIGHT}">

<defs>
  <linearGradient id="sky" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0%" stop-color="#071426"/>
    <stop offset="100%" stop-color="#102B2B"/>
  </linearGradient>
  <linearGradient id="water" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0%" stop-color="#123B49"/>
    <stop offset="100%" stop-color="#071B2D"/>
  </linearGradient>
</defs>

<rect width="100%" height="100%" fill="url(#sky)"/>

<!-- Moon -->
<circle cx="1050" cy="53" r="27" fill="#F4E5A5"/>
<circle cx="1062" cy="43" r="25" fill="#071426"/>

<!-- Stars -->
""")

rng = random.Random(42)

for _ in range(45):
    x = rng.randint(20, WIDTH - 20)
    y = rng.randint(15, 115)
    size = rng.choice([1, 2, 3])
    add(
        f'<rect x="{x}" y="{y}" width="{size}" '
        f'height="{size}" fill="#E9E8C4" opacity="0.8"/>'
    )

# Distant landscape
add("""
<path d="M0 125 L90 80 L170 120 L270 65 L370 120
         L480 85 L590 125 L710 70 L820 120
         L930 75 L1040 120 L1160 80 L1160 160 L0 160Z"
      fill="#102C37"/>

<!-- Meadow floor -->
<rect x="0" y="135" width="1160" height="195" fill="#0B211F"/>
<path d="M0 300 Q250 280 500 305 T1160 290 L1160 330 L0 330Z"
      fill="url(#water)"/>
""")

# --------------------------------------------------
# 5. Pixel-art trees and grass decoration
# --------------------------------------------------

# Tree on the left
add("""
<g shape-rendering="crispEdges">
  <rect x="25" y="65" width="15" height="90" fill="#65452E"/>
  <rect x="12" y="53" width="48" height="35" fill="#1E583A"/>
  <rect x="5" y="70" width="28" height="24" fill="#286B40"/>
  <rect x="40" y="45" width="35" height="30" fill="#347D42"/>
  <rect x="30" y="85" width="30" height="22" fill="#245B37"/>
  <rect x="18" y="62" width="8" height="8" fill="#8AB64A"/>
  <rect x="51" y="54" width="7" height="7" fill="#8AB64A"/>
</g>

<!-- Right-side plants -->
<g shape-rendering="crispEdges">
  <rect x="1090" y="125" width="8" height="30" fill="#285B38"/>
  <rect x="1078" y="117" width="12" height="8" fill="#397B3D"/>
  <rect x="1100" y="108" width="12" height="8" fill="#397B3D"/>
  <rect x="1120" y="130" width="8" height="20" fill="#245437"/>
</g>
""")

# --------------------------------------------------
# 6. Month labels
# --------------------------------------------------

month_names = [
    "Jan", "Feb", "Mar", "Apr", "May", "Jun",
    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"
]

add("""
<g font-family="monospace" font-size="12"
   fill="#C2D5C3">
""")

for week_index, week in enumerate(weeks):
    for day_data in week["contributionDays"]:
        day_date = date.fromisoformat(day_data["date"])
        if day_date.day == 1:
            x = X_START + week_index * STEP
            add(
                f'<text x="{x}" y="132">'
                f'{month_names[day_date.month - 1]}</text>'
            )
            break

add("</g>")

# Day labels
day_names = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]

add("""
<g font-family="monospace" font-size="11"
   fill="#A5B9AD">
""")

for i, name in enumerate(day_names):
    if i % 2 == 0:
        y = Y_START + i * STEP + 11
        add(f'<text x="55" y="{y}">{name}</text>')

add("</g>")

# --------------------------------------------------
# 7. Generate grass contribution tiles
# --------------------------------------------------

all_counts = [
    day["contributionCount"]
    for week in weeks
    for day in week["contributionDays"]
]

max_count = max(all_counts) if all_counts else 1

for week_index, week in enumerate(weeks):
    for day_index, day_data in enumerate(week["contributionDays"]):

        count = day_data["contributionCount"]
        day_date = day_data["date"]

        if count == 0:
            level = 0
        elif count <= max(1, max_count * 0.20):
            level = 1
        elif count <= max(2, max_count * 0.40):
            level = 2
        elif count <= max(3, max_count * 0.70):
            level = 3
        else:
            level = 4

        x = X_START + week_index * STEP
        y = Y_START + day_index * STEP

        rng = random.Random(day_date)

        # Grass tile
        rect(x, y, CELL, CELL, GRASS[level], 2)

        # Tiny grass blades
        for _ in range(2 + level):
            gx = x + rng.randint(2, 11)
            gy = y + rng.randint(3, 11)
            blade_height = rng.randint(2, 5)

            add(
                f'<path d="M{gx} {gy} l-1 -{blade_height}" '
                f'stroke="#9ACB61" stroke-width="1" '
                f'opacity="{0.25 + level * 0.12}"/>'
            )

        # Occasional tiny flowers
        if level > 0 and rng.random() < 0.13:
            fx = x + rng.randint(3, 10)
            fy = y + rng.randint(3, 10)
            flower = rng.choice(["#F5D9A5", "#E9A9B5", "#F2E9C6"])

            add(
                f'<rect x="{fx}" y="{fy}" width="2" height="2" '
                f'fill="{flower}"/>'
            )

# --------------------------------------------------
# 8. Animated pixel-art cat
# --------------------------------------------------

add("""
<!-- Animated cat -->
<g shape-rendering="crispEdges">
  <g>
    <animateTransform
      attributeName="transform"
      type="translate"
      values="0 0; 8 -5; 0 0; -5 2; 0 0"
      dur="5s"
      repeatCount="indefinite"/>

    <!-- Tail -->
    <g>
      <animateTransform
        attributeName="transform"
        type="rotate"
        values="0 235 83; 12 235 83; 0 235 83"
        dur="1.8s"
        repeatCount="indefinite"/>
      <rect x="229" y="68" width="7" height="19" fill="#D98C48"/>
      <rect x="224" y="65" width="8" height="7" fill="#F1C18A"/>
    </g>

    <!-- Body -->
    <rect x="225" y="82" width="34" height="18" fill="#D98C48"/>
    <rect x="232" y="94" width="21" height="8" fill="#F5E7CC"/>

    <!-- Head -->
    <rect x="254" y="75" width="19" height="18" fill="#D98C48"/>
    <rect x="254" y="69" width="7" height="8" fill="#D98C48"/>
    <rect x="267" y="69" width="7" height="8" fill="#D98C48"/>

    <!-- Face -->
    <rect x="260" y="82" width="3" height="3" fill="#14202A"/>
    <rect x="269" y="82" width="3" height="3" fill="#14202A"/>
    <rect x="264" y="87" width="3" height="2" fill="#F5D3B8"/>

    <!-- Paws -->
    <rect x="231" y="99" width="7" height="6" fill="#F5E7CC"/>
    <rect x="251" y="99" width="7" height="6" fill="#F5E7CC"/>
  </g>
</g>
""")

# --------------------------------------------------
# 9. Legend and footer
# --------------------------------------------------

add("""
<g font-family="monospace" font-size="11" fill="#B6CDBA">
  <text x="860" y="315">Less</text>
""")

for i, colour in enumerate(GRASS):
    rect(895 + i * 19, 302, 14, 14, colour, 2)

add("""
  <text x="1000" y="315">More</text>
  <text x="55" y="315" fill="#78978B">
    A little progress, every day.
  </text>
</g>
</svg>
""")

# --------------------------------------------------
# 10. Save SVG
# --------------------------------------------------

OUTPUT.parent.mkdir(parents=True, exist_ok=True)
OUTPUT.write_text("\n".join(svg), encoding="utf-8")

print(f"Generated {OUTPUT}")
print(f"Contribution days: {len(all_counts)}")
print(f"Maximum daily contributions: {max_count}")