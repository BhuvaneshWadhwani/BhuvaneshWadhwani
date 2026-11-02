"""Profile header: the night sky above the contribution forest.

Both images use the meadow's 480px-wide logical canvas, so when the README
shows them at 100% width their pixels are exactly the same size as the
meadow's. Sky, moon, treeline, canopy and stone all come from ``scene``.
"""
from __future__ import annotations

from html import escape

from . import rocket, scene
from .calendar import KERB_FRONT, KERB_FRONT_DK, KERB_HL, KERB_SHADE, KERB_TOP
from .pixels import Canvas, hash01, hexc, mix, noise2
from .sprites import draw_text, grass_tuft, text_width, title_bits
from .svgkit import PIXEL_STYLE, animated, cycle, discrete, img

W = scene.W
P = scene.P
AMBER = "#ffcf6e"
CANOPY = (P["canopy0"], P["canopy1"], P["canopy2"], P["canopy_rim"])


def _svg(w: int, h: int, label: str, body: list[str]) -> str:
    return "".join([
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" '
        f'width="{int(w * 2.5)}" height="{int(h * 2.5)}" shape-rendering="crispEdges" '
        f'role="img" aria-label="{escape(label)}">',
        PIXEL_STYLE, *body, "</svg>"])


def _twinkles(c: Canvas, count: int, seed: int, y_max: int) -> str:
    """Pick existing bright stars and make a few of them pulse."""
    out, found = [], 0
    for i in range(4000):
        x, y = int(hash01(i, 0, seed) * c.w), 2 + int(hash01(i, 1, seed) * (y_max - 2))
        if c.get(x, y) and c.get(x, y)[:3] in (P["star_hi"], P["star"]):
            dur = 2.4 + hash01(i, 2, seed) * 2.5
            out.append(animated(
                f'<rect x="{x}" y="{y}" width="1" height="1" fill="#e6ebe0" opacity="0"/>',
                discrete("opacity", (0, 1, 0), (0, .45, .6), round(dur, 1),
                         f' begin="{hash01(i, 3, seed) * 3:.1f}s"')))
            found += 1
            if found == count:
                break
    return "".join(out)


# --- title -------------------------------------------------------------------
TITLE_H = 52
LOGO = {"hi": hexc("#eef0dc"), "light": hexc("#d3d7c0"), "mid": hexc("#b5bba3"),
        "dark": hexc("#8f9783"), "low": hexc("#6d7565"), "outline": hexc("#070a09"),
        "shadow": hexc("#020303"), "moss": hexc("#3f5c33"), "moss_hi": hexc("#5d7f45")}


def _logo(text: str, ox: int, oy: int) -> tuple[Canvas, list[int]]:
    """Weathered moonlit stone lettering with moss on the upper edges."""
    bits, edges = title_bits(text)
    solid = {(ox + x, oy + y) for x, y in bits}
    c = Canvas(W, TITLE_H)
    ring = {(x + dx, y + dy) for x, y in solid for dx in (-1, 0, 1) for dy in (-1, 0, 1)} - solid
    for x, y in ring:
        c.put(x + 1, y + 1, LOGO["shadow"])
    for x, y in ring:
        c.put(x, y, LOGO["outline"])
    for x, y in solid:
        gy = y - oy
        if (x, y - 1) not in solid:
            colour = LOGO["hi"]
        elif (x, y + 1) not in solid:
            colour = LOGO["low"]
        else:
            colour = LOGO["light"] if gy < 7 else LOGO["mid"] if gy < 14 else LOGO["dark"]
        if noise2(x * 0.45, y * 0.45, 211) > 0.7:
            colour = mix(colour, LOGO["low"], 0.5)          # pitted stone
        c.put(x, y, colour)
    for x, y in solid:                                     # moss cushions on top edges
        if (x, y - 1) not in solid and noise2(x * 0.3, y * 0.2, 212) > 0.6:
            c.put(x, y, LOGO["moss_hi"])
            if (x, y + 1) in solid:
                c.put(x, y + 1, LOGO["moss"])
    return c, [ox + e for e in edges]


def title_svg(text: str = "Hi, I'm Bhuvanesh") -> str:
    c = Canvas(W, TITLE_H, fill=(0, 0, 0))
    scene.sky(c, horizon=TITLE_H, span=400, moon=(-99, -99, 1), star_rows=(2, TITLE_H - 2))
    scene.clumps(c, [(-4, -2, 12), (12, -5, 10), (28, -6, 7), (4, 9, 7),
                     (484, -2, 12), (468, -5, 10), (453, -6, 7), (477, 8, 7)], CANOPY, 201)
    for vx, length in ((9, 18), (20, 10), (471, 14), (460, 8)):
        for i in range(length):
            c.put(vx, 8 + i, P["vine"])
            if i % 3 == 1:
                c.put(vx + (1 if (i // 3) % 2 else -1), 8 + i, P["vine_leaf"])

    width = title_bits(text)[1][-1]
    ox, oy = (W - width) // 2, 15
    logo, edges = _logo(text, ox, oy)

    # typewriter reveal: a clip rect steps across one glyph at a time
    stops = [ox - 2] + [e + 2 for e in edges]
    keys = [i / len(stops) for i in range(len(stops))]
    typing = 2.2
    reveal = (f'<animate attributeName="width" values="{";".join(map(str, stops))}" '
              f'keyTimes="{";".join(f"{k:.4f}" for k in keys)}" calcMode="discrete" '
              f'dur="{typing}s" fill="freeze"/>')
    cursor_x = (f'<animate attributeName="x" values="{";".join(str(s + 1) for s in stops)}" '
                f'keyTimes="{";".join(f"{k:.4f}" for k in keys)}" calcMode="discrete" '
                f'dur="{typing}s" fill="freeze"/>')
    blink = discrete("opacity", (1, 0), (0, .5), 1.0)
    return _svg(W, TITLE_H, text, [
        img(c),
        f'<clipPath id="type"><rect x="0" y="0" width="{stops[-1]}" height="{TITLE_H}">'
        f'{reveal}</rect></clipPath>',
        f'<g clip-path="url(#type)">{img(logo)}</g>',
        f'<rect x="{stops[-1] + 1}" y="{oy}" width="3" height="21" fill="{AMBER}">'
        f'{cursor_x}{blink}</rect>',
        _twinkles(c, 7, 202, TITLE_H - 4),
    ])


# --- rocket launch -----------------------------------------------------------------
ROCKET_H = 136
MOON = (394, 30, 10)
PAD_Y = 121                 # top face of the launch platform
ROCKET_X = 234              # rocket sprite left edge; its nozzle centre is x + 6
LOOP = 9.0


def _launch_site(c: Canvas) -> None:
    # stone platform in 3/4 view, the same masonry as the courtyard kerbs
    x0, x1 = 214, 268
    for x in range(x0, x1 + 1):
        for y in range(PAD_Y, PAD_Y + 3):
            c.put(x, y, KERB_HL if y == PAD_Y else KERB_TOP)
        c.put(x, PAD_Y + 3, KERB_SHADE)
        for y in range(PAD_Y + 4, PAD_Y + 7):
            c.put(x, y, KERB_FRONT if y < PAD_Y + 6 else KERB_FRONT_DK)
        if (x - x0) % 9 == 4:
            for y in range(PAD_Y + 4, PAD_Y + 7):
                c.put(x, y, KERB_FRONT_DK)
    for x in range(ROCKET_X + 2, ROCKET_X + 11):           # scorched blast plate
        c.put(x, PAD_Y + 1, KERB_SHADE)
        c.put(x, PAD_Y + 2, mix(KERB_SHADE, P["night"], 0.5))
    # an old ruin tower serves as the gantry, with a timber arm to the rocket
    m = scene.Mask(c.w, c.h)
    for x in range(252, 261):
        top = 72 + int(abs(x - 255) * 0.8) + int(hash01(x, 0, 221) * 2)
        for y in range(top, PAD_Y):
            m.set(x, y)
    scene._bricks(c, m, 222)
    wood, wood_hi = hexc("#3a2c1f"), hexc("#5a4430")
    for x in range(ROCKET_X + 11, 252):
        c.put(x, 95, wood_hi)
        c.put(x, 96, wood)
    for i in range(7):                                     # diagonal brace
        c.put(251 - i, 97 + i, wood)
    c.put(256, 70, wood)                                   # lantern hook at the top
    c.put(256, 71, wood)


def _treeline(c: Canvas) -> None:
    m = scene.Mask(c.w, c.h)
    x, i = -10, 0
    while x < W + 10:
        i += 1
        if not 196 <= x <= 290:
            h = 18 + int(hash01(i, 0, 231) * 26)
            scene._fir(m, x, ROCKET_H + 3, h, h * 0.22, seed=i * 17)
        x += 9 + int(hash01(i, 1, 231) * 11)
    scene._shade(c, m, P["mid"], P["mid_tex"], P["mid_deep"], P["mid_rim"], P["mid_moss"], 232,
                 tex_scale=(0.3, 0.55), rim_chance=0.7)
    for y in range(PAD_Y + 7, ROCKET_H):                   # clearing floor around the pad
        for x in range(190, 296):
            if not m(x, y):
                c.put(x, y, scene.dither_pick([P["g0"], P["g1"], P["g2"]],
                                              0.4 + 0.5 * noise2(x * .2, y * .4, 233), x, y))
    for x in range(194, 292, 3):
        if hash01(x, 0, 234) > 0.3:
            grass_tuft(c, x, PAD_Y + 8 + int(hash01(x, 1, 234) * 6), x * 0.31, tall=3)


def _glow(w: int, h: int, colour, alpha: int) -> Canvas:
    g = Canvas(w, h)
    cx, cy = w / 2, h * 0.7
    for y in range(h):
        for x in range(w):
            d = (((x - cx) / (w / 2)) ** 2 + ((y - cy) / (h * 0.7)) ** 2) ** 0.5
            d += (scene.bayer(x, y) - 0.5) * 0.06             # stepped rings, ragged edges
            for limit, share in ((0.35, 1.0), (0.6, 0.6), (1.0, 0.3)):
                if d < limit:
                    g.put(x, y, (*colour, int(alpha * share)))
                    break
    return g


def _smoke(seed: int) -> Canvas:
    s = Canvas(18, 9)
    for y in range(9):
        for x in range(18):
            d = ((x - 9) / 9) ** 2 + ((y - 5) / 4.5) ** 2
            if d < 1 - hash01(x, y, seed) * 0.35:
                light = (x - 9) * 0.3 - (y - 5) * 0.6 > 0.3
                s.put(x, y, (*(hexc("#8f948c") if light else hexc("#5c625d")), 215))
    return s


def _text(label: str, colour) -> Canvas:
    t = Canvas(text_width(label) + 1, 6)
    draw_text(t, 0, 0, label, colour, shadow=hexc("#050806"))
    return t


def _keys(*seconds: float) -> list[float]:
    return [s / LOOP for s in seconds]


def _linear(attr: str, values, keys, dur: float, kind: str = "") -> str:
    tag = "animateTransform" if kind else "animate"
    type_ = f' type="{kind}"' if kind else ""
    return (f'<{tag} attributeName="{attr}"{type_} values="{";".join(values)}" '
            f'keyTimes="{";".join(f"{k:.4f}" for k in keys)}" dur="{dur}s" '
            f'repeatCount="indefinite"/>')


def rocket_svg() -> str:
    c = Canvas(W, ROCKET_H, fill=(0, 0, 0))
    scene.sky(c, horizon=ROCKET_H, span=150, moon=MOON, star_rows=(3, 96))
    scene.moon(c, MOON)
    scene.far_forest(c, line=101, bottom=ROCKET_H)
    scene.mist(c, 96, 124, 0.5, 5)
    _treeline(c)
    _launch_site(c)

    nozzle_x, nozzle_y = ROCKET_X + 6, PAD_Y
    ship = rocket.as_canvas(rocket.ROCKET)
    rocket_y = PAD_Y - ship.h
    flames = [rocket.as_canvas(f) for f in rocket.FLAMES]

    # countdown beside the gantry: T-3, T-2, T-1, LIFTOFF
    count = []
    labels = [("T-3", hexc("#c6cbb2")), ("T-2", hexc("#c6cbb2")), ("T-1", hexc("#c6cbb2")),
              ("LIFTOFF", hexc(AMBER))]
    for i, (label, colour) in enumerate(labels):
        vals = ["1" if j == i else "0" for j in range(5)]
        count.append(animated(img(_text(label, colour), 266, 100,
                                  f' opacity="{1 if i == 0 else 0}"'),
                              discrete("opacity", vals, _keys(0, 1, 2, 3, 5.5), LOOP)))

    lift = _linear("transform",
                   ["0 0", "0 0", "1 0", "0 0", "1 0", "0 0", "0 -3", "0 -14", "0 -40", "0 -90",
                    "0 -160", "0 -160"],
                   _keys(0, 2.6, 2.7, 2.8, 2.9, 3.0, 3.4, 4.0, 4.7, 5.4, 6.3, 9), LOOP, "translate")
    flame = (f'<g opacity="0">{discrete("opacity", (0, 1, 0), _keys(0, 2.8, 6.6), LOOP)}'
             f'{cycle(flames, 0.3, nozzle_x - 3, nozzle_y - 1)}</g>')
    glow = _glow(120, 44, hexc("#ffb45e"), 70)
    glow_el = animated(img(glow, nozzle_x - 60, nozzle_y - 31, ' opacity="0"'),
                       _linear("opacity", ["0", "0", "1", ".7", "0", "0"],
                               _keys(0, 2.8, 3.3, 4.6, 6.0, 9), LOOP))
    puffs = []
    for side, seed in ((-1, 241), (1, 242)):
        s = _smoke(seed)
        x0 = nozzle_x - 9 + side * 8
        puffs.append(
            '<g opacity="0">'
            + _linear("opacity", ["0", "0", ".95", ".55", "0", "0"], _keys(0, 3.0, 3.6, 5.2, 7.0, 9), LOOP)
            + _linear("transform", ["0 0", "0 0", f"{side * 8} -1", f"{side * 20} -4", f"{side * 26} -6",
                                    f"{side * 26} -6"], _keys(0, 3.0, 3.8, 5.2, 7.0, 9), LOOP, "translate")
            + img(s, x0, nozzle_y - 6) + "</g>")

    sats = []
    for art, y, dur, start in ((rocket.SATELLITE, 18, 46, -20), (rocket.PROBE, 52, 63, 500)):
        s = rocket.as_canvas(art)
        end = W + 20 if start < 0 else -20
        sats.append(
            f'<g>{_linear("transform", [f"{start} {y}", f"{end} {y - 6}"], [0, 1], dur, "translate")}'
            f'{img(s)}'
            + animated(f'<rect x="{s.w // 2}" y="-1" width="1" height="1" fill="#b8483a" opacity="0"/>',
                       discrete("opacity", (0, 1, 0), (0, .5, .62), 1.6))
            + "</g>")

    lantern = animated('<rect x="256" y="69" width="1" height="1" fill="#ffcf6e"/>',
                       discrete("opacity", (1, .35), (0, .5), 1.2))
    return _svg(W, ROCKET_H, "Pixel-art rocket launching at night from an old stone gantry in a moonlit forest clearing", [
        img(c),
        *sats,
        glow_el,
        lantern,
        f'<g>{lift}{img(ship, ROCKET_X, rocket_y)}{flame}</g>',
        *puffs,
        *count,
        _twinkles(c, 9, 243, 90),
    ])
