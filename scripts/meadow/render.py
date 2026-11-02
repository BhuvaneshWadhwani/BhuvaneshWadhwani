"""Compose the painted scene and its animated layers into one SVG.

Static art is a single embedded PNG (rendered with nearest-neighbour scaling).
Only what moves sits on top as SVG: drifting mist, the cat and its lantern
light, foreground grass the cat walks behind, and fireflies. Every animation
starts from a sensible frame, so the image still reads if SMIL is ignored.
"""
from __future__ import annotations

from datetime import date
from html import escape

from . import cat, rocket, scene
from .calendar import (STONE_W, TOP_H, FRONT_H, arrange, draw_courtyard,
                       draw_day_labels, draw_legend, make_layout)
from .pixels import Canvas, hash01, hexc
from .sprites import draw_text, text_width
from .svgkit import PIXEL_STYLE, animated, cycle, discrete, img, linear

W, H, SCALE = scene.W, scene.H, 2.5
TEXT, TEXT_DIM, TEXT_SHADOW = hexc("#c6cbb2"), hexc("#86927f"), hexc("#050806")

# Cat timeline (seconds): walk right, pause, walk back, pause.
CYCLE = 50.0
X_START, X_END = 56, 306
KEYS = (0, 20 / CYCLE, 26 / CYCLE, 46 / CYCLE, 1)
STEP = 0.6             # one full four-frame stride


def paint(days: list[dict], total: int):
    cells = arrange(days)
    lay = make_layout(len(cells) // 7, W)
    base = Canvas(W, H, fill=(0, 0, 0))
    occluder = Canvas(W, H)

    scene.sky(base)
    scene.moon(base)
    sky_only = [row[:] for row in base.px]      # what shows through gaps in the trees
    scene.far_forest(base)
    scene.mist(base, 58, 98, 0.6, 1)
    scene.tower(base)
    scene.mid_forest(base)
    scene.mist(base, 84, 106, 0.42, 2)
    scene.ruins(base)
    scene.moonbeams(base)
    scene.undergrowth(base)
    scene.ground(base)
    scene.path(base, occluder)
    tiles = draw_courtyard(base, cells, lay)
    scene.trunks(base, lay)
    scene.canopy(base)
    scene.foreground(base, lay)
    scene.corner_foliage(base)

    stones = (lay.gx - 1, lay.gy - 1, lay.gx + lay.grid_w, lay.grid_bottom)
    scene.vignette(base, skip=lambda x, y: stones[0] <= x <= stones[2] and stones[1] <= y <= stones[3])

    draw_day_labels(base, lay, TEXT_DIM, TEXT_SHADOW)
    ty = lay.bottom + 7
    draw_text(base, lay.left, ty, "A YEAR IN THE WILDS", TEXT, shadow=TEXT_SHADOW)
    draw_text(base, lay.left, ty + 8, f"{total:,} CONTRIBUTIONS IN THE LAST YEAR",
              TEXT_DIM, shadow=TEXT_SHADOW)
    legend_w = text_width("LESS") + 4 + 5 * (STONE_W + 3) + 2 + text_width("MORE")
    draw_legend(base, lay.right - legend_w, ty + 3, TEXT_DIM, TEXT_SHADOW)
    return base, occluder, tiles, lay, sky_only


def _state(index: int, body: str) -> str:
    vals = ";".join("1" if j == index else "0" for j in range(4))
    keys = ";".join(f"{k:.4f}" for k in KEYS[:4])
    return (f'<g opacity="{1 if index == 0 else 0}"><animate attributeName="opacity" '
            f'values="{vals}" keyTimes="{keys}" calcMode="discrete" dur="{CYCLE}s" '
            f'repeatCount="indefinite"/>{body}</g>')


def cat_layer() -> str:
    walk_r = [cat.frame(i, (-1, 0, 1, 0)[i]) for i in range(4)]
    idle_r = [cat.frame(0, t, still=True) for t in (0, 1, 0, -1)]
    walk_l = [cat.flipped(f) for f in walk_r]
    idle_l = [cat.flipped(f) for f in idle_r]
    glow = scene.lantern_glow()
    lantern_r, lantern_l = 22, cat.W - 1 - 22
    flicker = ('<animate attributeName="opacity" values="1;.8;1;.9;1" dur="2.3s" '
               'repeatCount="indefinite"/>')

    def glow_at(lx: int) -> str:
        return img(glow, lx - glow.w // 2, 14 - glow.h // 2).replace(
            "/>", f">{flicker}</image>")

    y = scene.PATH_Y - (cat.H - 1)
    shadow = scene.cat_shadow()
    states = [
        _state(0, cycle(walk_r, STEP) + glow_at(lantern_r)),
        _state(1, cycle(idle_r, 2.8) + glow_at(lantern_r)),
        _state(2, cycle(walk_l, STEP) + glow_at(lantern_l)),
        _state(3, cycle(idle_l, 2.8) + glow_at(lantern_l)),
    ]
    move = (f'<animateTransform attributeName="transform" type="translate" '
            f'values="{X_START} {y};{X_END} {y};{X_END} {y};{X_START} {y};{X_START} {y}" '
            f'keyTimes="{";".join(f"{k:.4f}" for k in KEYS)}" dur="{CYCLE}s" '
            f'repeatCount="indefinite"/>')
    return (f'<g id="explorer" transform="translate({X_START} {y})">{move}'
            f'{img(shadow, 3, cat.H - 2)}{"".join(states)}</g>')


# Distant launch (seconds): ignition flare, climb, trail lingers and fades.
LAUNCH = 36.0
LAUNCH_X = 249          # an open column of sky between the treetops
LAUNCH_Y = 74           # rocket top when it starts, hidden behind the far treeline
HORIZON = 92            # nothing from the launch is drawn below this row


def launch_layer(base: Canvas, sky_only: list) -> str:
    """A far-off rocket rising beyond the forest, echoing the header.

    Everything painted in front of the sky near the launch column is copied
    into a cut-out drawn over the rocket, so it climbs *behind* the treeline
    and the mid-forest and disappears into the canopy.
    """
    x0, x1 = LAUNCH_X - 15, LAUNCH_X + 15
    cut = Canvas(x1 - x0 + 1, HORIZON + 1)
    for y in range(HORIZON + 1):
        for x in range(x0, x1 + 1):
            if base.px[y][x] != sky_only[y][x]:
                cut.put(x - x0, y, base.px[y][x])

    keys = lambda *s: [v / LAUNCH for v in s]
    ship = rocket.as_canvas(rocket.DISTANT)
    flames = [rocket.as_canvas(f) for f in rocket.DISTANT_FLAMES]
    trail = scene.rocket_trail()
    rx = LAUNCH_X - ship.w // 2

    climb = linear("transform", [f"0 {LAUNCH_Y - d}" for d in (0, 0, 6, 20, 45, 84, 84)],
                   keys(0, 1.5, 3.5, 5.5, 7.5, 10, 36), LAUNCH, "translate")
    craft = ('<g opacity="0">' + discrete("opacity", (0, 1, 0), keys(0, 1.5, 10.5), LAUNCH)
             + img(ship, rx, 0) + cycle(flames, 0.2, rx, ship.h) + "</g>")
    smoke = ('<g opacity="0">'
             + linear("opacity", ["0", "0", "1", "1", "0", "0"], keys(0, 1.5, 2.2, 11, 22, 36), LAUNCH)
             + '<g>' + linear("transform", ["0 0", "0 0", "4 0", "4 0"], keys(0, 10, 22, 36), LAUNCH,
                               "translate")
             + img(trail, LAUNCH_X - trail.w // 2, ship.h + 1) + "</g></g>")
    glow = scene.ignition_glow()
    flare = animated(img(glow, LAUNCH_X - glow.w // 2, LAUNCH_Y - 10, ' opacity="0"'),
                     linear("opacity", ["0", "0", ".5", "1", ".6", "1", ".3", "0", "0"],
                            keys(0, .2, .6, 1.0, 1.3, 1.7, 3.5, 5.5, 36), LAUNCH))
    return (f'<clipPath id="sky"><rect x="{x0}" y="0" width="{cut.w}" height="{HORIZON + 1}"/></clipPath>'
            f'<g clip-path="url(#sky)"><g>{climb}{smoke}{craft}</g></g>'
            f'{img(cut, x0, 0)}{flare}')


def fireflies() -> str:
    spots = [(118, 62), (196, 84), (250, 70), (338, 92), (430, 78), (88, 96),
             (14, 140), (466, 150), (150, 196), (342, 194), (406, 206), (58, 208)]
    out = []
    for i, (x, y) in enumerate(spots):
        r = lambda k: hash01(i, k, 191)
        path = ";".join(f"{round((r(k) - .5) * 14)} {round((r(k + 9) - .5) * 8)}" for k in range(5))
        path += ";" + path.split(";")[0]
        out.append(
            f'<g><animateTransform attributeName="transform" type="translate" values="{path}" '
            f'dur="{12 + int(r(20) * 9)}s" repeatCount="indefinite"/>'
            f'<g opacity=".7"><animate attributeName="opacity" values="0;.95;.4;.9;0" '
            f'dur="{4 + int(r(21) * 4)}s" begin="{r(22) * 4:.1f}s" repeatCount="indefinite"/>'
            f'<rect x="{x - 1}" y="{y - 1}" width="3" height="3" fill="#e9d27e" opacity=".22"/>'
            f'<rect x="{x}" y="{y}" width="1" height="1" fill="#f6e9a8"/></g></g>')
    return "".join(out)


def tooltips(tiles: list[dict]) -> str:
    out = ['<g fill="#fff" fill-opacity="0">']
    for t in tiles:
        d = date.fromisoformat(t["date"])
        n = t["count"]
        label = f'{d.strftime("%a %d %b %Y")}: {n} contribution{"" if n == 1 else "s"}'
        out.append(f'<rect x="{t["x"]}" y="{t["y"]}" width="{STONE_W}" '
                   f'height="{TOP_H + FRONT_H}"><title>{escape(label)}</title></rect>')
    out.append("</g>")
    return "".join(out)


def build_svg(days: list[dict], total: int) -> str:
    base, occluder, tiles, lay, sky_only = paint(days, total)
    mist = scene.mist_overlay(W + 40)
    title = f"Dark fantasy pixel-art forest: {total:,} GitHub contributions in the last year"
    return "".join([
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" '
        f'width="{int(W * SCALE)}" height="{int(H * SCALE)}" shape-rendering="crispEdges" '
        f'role="img" aria-labelledby="t d">',
        f'<title id="t">{escape(title)}</title>',
        '<desc id="d">A moonlit enchanted forest with ancient ruins. The contribution calendar '
        'is an overgrown flagstone courtyard: one stone per day, mossier and brighter with more '
        'contributions. An orange cat explorer with a cloak, pack and lantern walks the path.</desc>',
        PIXEL_STYLE,
        img(base),
        launch_layer(base, sky_only),
        f'<g opacity=".9">{img(mist, -20, 92)}<animateTransform attributeName="transform" '
        'type="translate" values="0 0;14 0;0 0" dur="40s" repeatCount="indefinite"/></g>',
        cat_layer(),
        img(occluder),
        fireflies(),
        tooltips(tiles),
        "</svg>",
    ])
