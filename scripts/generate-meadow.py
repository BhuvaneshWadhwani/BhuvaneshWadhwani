
import json
import os
import random
import urllib.request
from datetime import date, timedelta
from pathlib import Path
from xml.sax.saxutils import escape

# ============================================================
# CONFIGURATION
# ============================================================

USERNAME = "BhuvaneshWadhwani"
TOKEN = os.environ["GITHUB_TOKEN"]

OUTPUT = Path("dist/contribution-meadow.svg")

WIDTH = 1160
HEIGHT = 390

CELL = 14
GAP = 4
STEP = CELL + GAP

X_START = 105
Y_START = 165

GRASS = [
    "#172D27",  # No contributions
    "#28523A",  # Low
    "#397747",  # Moderate
    "#609C49",  # High
    "#A8CF58",  # Very high
]

random.seed(42)

# ============================================================
# 1. FETCH REAL GITHUB CONTRIBUTION DATA
# ============================================================

today = date.today()
start_date = today - timedelta(days=364)

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
        "from": start_date.isoformat() + "T00:00:00Z",
        "to": today.isoformat() + "T23:59:59Z",
    },
}

request = urllib.request.Request(
    "https://api.github.com/graphql",
    data=json.dumps(payload).encode("utf-8"),
    headers={
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json",
        "User-Agent": "GitHub-Contribution-Meadow",
    },
)

with urllib.request.urlopen(request, timeout=30) as response:
    result = json.loads(response.read().decode("utf-8"))

if result.get("errors"):
    raise RuntimeError(f"GitHub API error: {result['errors']}")

user = result.get("data", {}).get("user")

if not user:
    raise RuntimeError(f"GitHub user not found: {USERNAME}")

calendar = user["contributionsCollection"]["contributionCalendar"]
weeks = calendar["weeks"]

if not weeks:
    raise RuntimeError("GitHub returned an empty contribution calendar.")

total_contributions = calendar["totalContributions"]

print(f"Retrieved {total_contributions} contributions.")
print(f"Retrieved {len(weeks)} calendar weeks.")

# ============================================================
# 2. SVG HELPERS
# ============================================================

svg = []


def add(value):
    svg.append(value)


def rect(x, y, w, h, fill, radius=0, extra=""):
    add(
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" '
        f'rx="{radius}" fill="{fill}" {extra}/>'
    )


def text_element(x, y, content, size=12, colour="#C4D5C3",
                 extra=""):
    add(
        f'<text x="{x}" y="{y}" font-family="monospace" '
        f'font-size="{size}" fill="{colour}" {extra}>'
        f'{escape(str(content))}</text>'
    )


# ============================================================
# 3. BACKGROUND AND SVG DEFINITIONS
# ============================================================

add(f'''<svg xmlns="http://www.w3.org/2000/svg"
     width="{WIDTH}" height="{HEIGHT}"
     viewBox="0 0 {WIDTH} {HEIGHT}">

<defs>

  <linearGradient id="sky" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0%" stop-color="#071321"/>
    <stop offset="65%" stop-color="#102C35"/>
    <stop offset="100%" stop-color="#173C36"/>
  </linearGradient>

  <linearGradient id="pond" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0%" stop-color="#17434A"/>
    <stop offset="100%" stop-color="#091C2A"/>
  </linearGradient>

  <linearGradient id="moonlight" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0%" stop-color="#D8E7B6" stop-opacity="0.14"/>
    <stop offset="100%" stop-color="#D8E7B6" stop-opacity="0"/>
  </linearGradient>

  <filter id="softGlow">
    <feGaussianBlur stdDeviation="3"/>
  </filter>

</defs>

<rect width="{WIDTH}" height="{HEIGHT}" fill="url(#sky)"/>
''')

# ============================================================
# 4. STARS AND MOON
# ============================================================

for _ in range(65):
    x = random.randint(10, WIDTH - 10)
    y = random.randint(10, 115)
    size = random.choice([1, 1, 2, 3])

    colour = random.choice(["#E7EBCB", "#A9C9C0", "#F5DDA2"])

    rect(x, y, size, size, colour, extra='opacity="0.8"')

# Moon glow
add('<circle cx="1035" cy="65" r="48" fill="#DCE6B5" opacity="0.08" filter="url(#softGlow)"/>')

# Pixel-style crescent moon
add("""
<g shape-rendering="crispEdges">
  <circle cx="1035" cy="65" r="27" fill="#E8E6B8"/>
  <circle cx="1048" cy="55" r="24" fill="#0A1D2B"/>
  <rect x="1018" y="49" width="5" height="5" fill="#FFF4CC" opacity="0.6"/>
  <rect x="1026" y="83" width="4" height="4" fill="#FFF4CC" opacity="0.5"/>
</g>
""")

# ============================================================
# 5. DISTANT MOUNTAINS AND FOREST
# ============================================================

add("""
<!-- Distant mountains -->
<path d="
M0 150 L75 92 L135 130 L225 75 L305 132
L390 95 L475 140 L575 80 L675 135
L775 90 L865 135 L965 88 L1060 135
L1160 85 L1160 225 L0 225 Z"
fill="#122D37"/>

<!-- Distant tree line -->
<path d="
M0 165 L35 115 L70 165 L105 110 L145 165
L180 120 L215 165 L255 105 L295 165
L335 125 L375 165 L415 112 L455 165
L495 125 L535 165 L575 105 L615 165
L655 120 L695 165 L735 108 L775 165
L815 120 L855 165 L895 105 L935 165
L975 125 L1015 165 L1055 110 L1095 165
L1135 120 L1160 155 L1160 230 L0 230 Z"
fill="#173E34"/>

<!-- Moonlight -->
<rect x="0" y="105" width="1160" height="115"
      fill="url(#moonlight)"/>

<!-- Main meadow -->
<rect x="0" y="215" width="1160" height="175"
      fill="#102C25"/>
""")

# Foreground forest trees at both edges
add("""
<g shape-rendering="crispEdges">

  <!-- Left large tree -->
  <rect x="24" y="83" width="17" height="174" fill="#533D2E"/>
  <rect x="8" y="105" width="48" height="40" fill="#17482F"/>
  <rect x="0" y="132" width="55" height="39" fill="#205C39"/>
  <rect x="16" y="70" width="40" height="35" fill="#286A40"/>
  <rect x="42" y="92" width="36" height="40" fill="#1B5435"/>
  <rect x="8" y="114" width="9" height="8" fill="#60964A"/>
  <rect x="42" y="80" width="8" height="7" fill="#78A84C"/>

  <!-- Right large tree -->
  <rect x="1110" y="85" width="17" height="172" fill="#533D2E"/>
  <rect x="1082" y="105" width="60" height="40" fill="#17482F"/>
  <rect x="1090" y="70" width="55" height="38" fill="#286A40"/>
  <rect x="1072" y="132" width="65" height="39" fill="#205C39"/>
  <rect x="1090" y="91" width="9" height="8" fill="#60964A"/>
  <rect x="1120" y="78" width="8" height="7" fill="#78A84C"/>

</g>
""")

# ============================================================
# 6. MONTH AND WEEKDAY LABELS
# ============================================================

month_names = [
    "Jan", "Feb", "Mar", "Apr", "May", "Jun",
    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
]

day_names = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]

for i, name in enumerate(day_names):
    if i % 2 == 0:
        text_element(
            47,
            Y_START + i * STEP + 11,
            name,
            size=10,
            colour="#A7C1A8",
        )

for week_index, week in enumerate(weeks):
    for day in week["contributionDays"]:
        day_date = date.fromisoformat(day["date"])

        if day_date.day == 1:
            x = X_START + week_index * STEP

            text_element(
                x,
                153,
                month_names[day_date.month - 1],
                size=11,
                colour="#C5D5B9",
            )
            break

# ============================================================
# 7. CONTRIBUTION GRASS TILES
# ============================================================

level_map = {
    "NONE": 0,
    "FIRST_QUARTILE": 1,
    "SECOND_QUARTILE": 2,
    "THIRD_QUARTILE": 3,
    "FOURTH_QUARTILE": 4,
}

for week_index, week in enumerate(weeks):
    for day_index, day in enumerate(week["contributionDays"]):

        level = level_map.get(day["contributionLevel"], 0)
        day_date = day["date"]

        x = X_START + week_index * STEP
        y = Y_START + day_index * STEP

        tile_rng = random.Random(day_date)

        # Unique clip region for grass details
        clip_id = f"tile-{week_index}-{day_index}"

        add(f"""
        <defs>
          <clipPath id="{clip_id}">
            <rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="2"/>
          </clipPath>
        </defs>
        """)

        add(f'<g clip-path="url(#{clip_id})">')

        # Base grass colour
        rect(x, y, CELL, CELL, GRASS[level])

        # Grass texture
        blade_count = 1 + level * 2

        for _ in range(blade_count):
            gx = x + tile_rng.randint(1, 13)
            gy = y + tile_rng.randint(5, 14)
            height = tile_rng.randint(2, 5)

            add(
                f'<path d="M{gx} {gy} l-1 -{height}" '
                f'stroke="#B6DC76" stroke-width="1" '
                f'opacity="{0.22 + level * 0.13}"/>'
            )

        # Small darker grass patches
        if level > 0:
            for _ in range(1 + level):
                gx = x + tile_rng.randint(2, 11)
                gy = y + tile_rng.randint(3, 12)

                rect(
                    gx,
                    gy,
                    2,
                    2,
                    "#173B2B",
                    extra='opacity="0.35"',
                )

        # Flowers become more common at higher levels
        if level >= 2 and tile_rng.random() < 0.16:
            fx = x + tile_rng.randint(3, 10)
            fy = y + tile_rng.randint(3, 10)

            flower = tile_rng.choice([
                "#F2D7A0",
                "#EAA8B4",
                "#F2EAC4",
            ])

            rect(fx, fy, 2, 2, flower)

        add("</g>")

        # Subtle tile border
        add(
            f'<rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" '
            f'rx="2" fill="none" stroke="#C3D8A0" '
            f'stroke-opacity="0.12" stroke-width="0.6"/>'
        )

# ============================================================
# 8. FOREST FLOOR, FLOWERS AND MUSHROOMS
# ============================================================

for _ in range(85):
    x = random.randint(75, 1080)
    y = random.randint(300, 375)

    # Small grass tufts
    add(
        f'<path d="M{x} {y} l-3 -5 M{x} {y} l2 -7 '
        f'M{x} {y} l5 -4" stroke="#477B43" '
        f'stroke-width="2" fill="none" opacity="0.8"/>'
    )

# Mushrooms
add("""
<g shape-rendering="crispEdges">
  <rect x="145" y="318" width="7" height="12" fill="#E7D5AD"/>
  <rect x="138" y="313" width="21" height="7" fill="#C96B50"/>
  <rect x="142" y="310" width="13" height="4" fill="#E18A61"/>
  <rect x="145" y="314" width="3" height="2" fill="#FFF0C7"/>

  <rect x="1000" y="333" width="7" height="11" fill="#E7D5AD"/>
  <rect x="994" y="329" width="18" height="6" fill="#C96B50"/>
  <rect x="998" y="326" width="10" height="4" fill="#E18A61"/>
</g>
""")

# ============================================================
# 9. POND AND WATER REFLECTIONS
# ============================================================

add("""
<path d="
M270 360 Q390 320 515 350
Q650 375 760 345
Q875 315 1000 360
L1000 390 L270 390 Z"
fill="url(#pond)"/>

<g stroke="#5B9A92" stroke-width="2" opacity="0.5">
  <path d="M365 365 h45"/>
  <path d="M480 375 h65"/>
  <path d="M685 360 h55"/>
  <path d="M800 375 h35"/>
  <path d="M900 355 h48"/>
</g>

<!-- Lily pads -->
<g fill="#43865A">
  <ellipse cx="580" cy="365" rx="15" ry="5"/>
  <ellipse cx="850" cy="380" rx="12" ry="4"/>
</g>

<g fill="#E8C6A0">
  <rect x="579" y="359" width="3" height="3"/>
  <rect x="847" y="375" width="3" height="3"/>
</g>
""")

# ============================================================
# 10. ANIMATED ORANGE-AND-WHITE CAT
# ============================================================

add("""
<!-- Cat walking across the meadow -->
<g id="cat" shape-rendering="crispEdges">

  <animateTransform
    attributeName="transform"
    type="translate"
    values="0 0; 520 0; 520 0; 0 0"
    keyTimes="0; 0.45; 0.55; 1"
    dur="24s"
    repeatCount="indefinite"/>

  <!-- Tail -->
  <g transform="translate(0 0)">
    <rect x="0" y="0" width="7" height="15"
          fill="#E28D45" transform="translate(217 103)"/>
    <rect x="0" y="0" width="7" height="6"
          fill="#F5D8B3" transform="translate(217 115)"/>

    <animateTransform
      attributeName="transform"
      additive="sum"
      type="rotate"
      values="-12 220 115; 14 220 115; -12 220 115"
      dur="1.5s"
      repeatCount="indefinite"/>
  </g>

  <!-- Body -->
  <rect x="225" y="105" width="33" height="18" fill="#E28D45"/>
  <rect x="233" y="116" width="19" height="7" fill="#F5E7CC"/>
  <rect x="240" y="105" width="8" height="6" fill="#F5E7CC"/>

  <!-- Head -->
  <rect x="254" y="99" width="22" height="21" fill="#E28D45"/>
  <rect x="255" y="93" width="7" height="9" fill="#E28D45"/>
  <rect x="268" y="93" width="8" height="9" fill="#E28D45"/>

  <!-- Inner ears -->
  <rect x="257" y="96" width="3" height="4" fill="#F4B3A2"/>
  <rect x="270" y="96" width="3" height="4" fill="#F4B3A2"/>

  <!-- Face -->
  <rect x="258" y="106" width="3" height="3" fill="#17202A"/>
  <rect x="269" y="106" width="3" height="3" fill="#17202A"/>
  <rect x="263" y="112" width="4" height="2" fill="#F4B3A2"/>

  <!-- White muzzle -->
  <rect x="260" y="111" width="4" height="4" fill="#F5E7CC"/>
  <rect x="266" y="111" width="4" height="4" fill="#F5E7CC"/>

  <!-- Legs -->
  <g>
    <rect x="229" y="120" width="7" height="8" fill="#E28D45"/>
    <rect x="250" y="120" width="7" height="8" fill="#F5E7CC"/>

    <animateTransform
      attributeName="transform"
      type="translate"
      values="0 0; 0 -3; 0 0"
      dur="0.45s"
      repeatCount="indefinite"/>
  </g>

  <!-- Front paw -->
  <rect x="266" y="119" width="8" height="8" fill="#F5E7CC"/>

  <!-- Cat shadow -->
  <ellipse cx="250" cy="132" rx="31" ry="3"
           fill="#061713" opacity="0.55"/>

</g>
""")

# ============================================================
# 11. ANIMATED FIREFLIES
# ============================================================

for i in range(12):
    x = random.randint(90, 1080)
    y = random.randint(90, 300)
    delay = random.randint(0, 8)

    add(f"""
    <circle cx="{x}" cy="{y}" r="2.2"
            fill="#D9F59A" opacity="0.15">
      <animate attributeName="opacity"
               values="0.1;0.95;0.1"
               dur="{random.randint(2, 5)}s"
               begin="-{delay}s"
               repeatCount="indefinite"/>
      <animate attributeName="cy"
               values="{y};{y - 9};{y}"
               dur="{random.randint(3, 6)}s"
               begin="-{delay}s"
               repeatCount="indefinite"/>
    </circle>
    """)

# ============================================================
# 12. CONTRIBUTION LEGEND
# ============================================================

text_element(825, 372, "Less", size=11, colour="#B4C9AD")

for i, colour in enumerate(GRASS):
    rect(860 + i * 20, 358, 15, 15, colour, radius=2)

text_element(970, 372, "More", size=11, colour="#B4C9AD")

# Total contribution label
text_element(
    48,
    372,
    f"{total_contributions:,} contributions in the last year",
    size=11,
    colour="#9CB7A3",
)

# ============================================================
# 13. SAVE SVG
# ============================================================

add("</svg>")

OUTPUT.parent.mkdir(parents=True, exist_ok=True)
OUTPUT.write_text("\n".join(svg), encoding="utf-8")

print(f"Generated: {OUTPUT}")
print(f"Contribution total: {total_contributions}")
print(f"Calendar weeks: {len(weeks)}")
print("Meadow generation completed successfully.")
