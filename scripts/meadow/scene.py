"""The forest environment, painted pixel by pixel.

Depth layers, back to front:
    sky + moon -> far treeline -> ruined tower -> mist -> mid forest
    -> broken arch / pillar -> undergrowth -> clearing floor + path
    -> ancient framing trunks -> canopy -> (courtyard calendar) -> foreground

Moonlight comes from the upper right, so rims are lit on top/right edges.
Gradients are expressed through ordered dithering between palette colours
rather than smooth blends, which keeps everything on one pixel grid.
"""
from __future__ import annotations

import math

from .pixels import Canvas, bayer, fbm1, fbm2, hash01, hexc, mix, noise1, noise2
from .sprites import FERNS, MUSHROOMS, grass_tuft

W, H = 480, 216
MOON = (398, 31, 10)
PATH_Y = 107            # the row the cat's paws rest on

P = {k: hexc(v) for k, v in {
    "sky0": "#04060a", "sky1": "#080c14", "sky2": "#0c121c", "sky3": "#111a25",
    "halo": "#2a3746", "star": "#7d8a99", "star_hi": "#c8cfd6",
    "moon": "#dcdfca", "moon_lo": "#bfc4ae", "moon_dk": "#a6ac98", "moon_shadow": "#2b333b",
    "far": "#0f1822", "far_tex": "#121d29", "far_rim": "#1b2735",
    "mist": "#3c4b57",
    "tower": "#19212b", "tower_hi": "#232e3a", "tower_dk": "#11171f", "mortar": "#0d1218",
    "window": "#e0a04c", "window_hi": "#f6cf7c", "warm": "#4a3220",
    "mid": "#0a1315", "mid_tex": "#0e1a1b", "mid_deep": "#070e10",
    "mid_rim": "#1a2c2a", "mid_moss": "#24392e",
    "ruin": "#262c2c", "ruin_hi": "#363f3d", "ruin_edge": "#4b5550", "ruin_dk": "#191e1e",
    "ruin_mortar": "#121615", "moss": "#26382a", "moss_hi": "#3a5434",
    "under": "#0b1512", "under_hi": "#18281f", "under_rim": "#25392b",
    "g0": "#0d130f", "g1": "#131b14", "g2": "#19241a", "g3": "#203020",
    "leaf": "#3b2c1c", "leaf_hi": "#56402a", "pebble": "#2b302b", "pebble_hi": "#3d433c",
    "path0": "#1c1b16", "path1": "#24231c", "path2": "#2d2b23", "path3": "#38362c",
    "bark0": "#0b0a09", "bark1": "#13110f", "bark2": "#1c1915", "bark3": "#2a2620",
    "bark_rim": "#3c3d36", "bark_moss": "#22301f", "bark_moss_hi": "#344a2c",
    "canopy0": "#040706", "canopy1": "#08100d", "canopy2": "#0e1914", "canopy_rim": "#1b2d23",
    "vine": "#0f1b15", "vine_leaf": "#1b3024", "vine_hi": "#2c4733",
    "beam": "#8193a0", "night": "#020403",
}.items()}


class Mask:
    def __init__(self) -> None:
        self.on = [[False] * W for _ in range(H)]

    def set(self, x: int, y: int) -> None:
        if 0 <= x < W and 0 <= y < H:
            self.on[y][x] = True

    def __call__(self, x: int, y: int) -> bool:
        return 0 <= x < W and 0 <= y < H and self.on[y][x]

    def span(self, x0: int, x1: int, y: int) -> None:
        for x in range(x0, x1 + 1):
            self.set(x, y)

    def pixels(self):
        for y in range(H):
            row = self.on[y]
            for x in range(W):
                if row[x]:
                    yield x, y


def clamp(v: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return lo if v < lo else hi if v > hi else v


def dither_pick(colours, t: float, x: int, y: int, spread: float = 0.3,
                threshold=None):
    """Pick from an ordered ramp at position t in [0, 1].

    Only the middle ``spread`` of each step is dithered, so ramps read as clean
    bands with short transitions instead of a field of checkerboard. Pass a
    ``threshold`` (e.g. clustered noise) for organic rather than ordered mixing.
    """
    pos = clamp(t) * (len(colours) - 1)
    i = int(pos)
    if i >= len(colours) - 1:
        return colours[-1]
    f = clamp((pos - i - 0.5) / spread + 0.5)
    return colours[i + 1] if (bayer(x, y) if threshold is None else threshold) < f else colours[i]


# --- sky -------------------------------------------------------------------
def sky(c: Canvas) -> None:
    mx, my, mr = MOON
    ramp = [P["sky0"], P["sky1"], P["sky2"], P["sky3"]]
    rings = ((mr + 3, 0.34), (mr + 8, 0.22), (mr + 17, 0.13), (mr + 31, 0.06))
    for y in range(110):
        for x in range(W):
            colour = dither_pick(ramp, (y / 105) ** 1.1, x, y)
            d = math.hypot(x - mx, (y - my) * 1.1)
            for radius, t in rings:                     # banded halo, no checkerboard
                if d < radius + (bayer(x, y) - 0.5) * 2:
                    colour = mix(colour, P["halo"], t)
                    break
            c.put(x, y, colour)
    for y in range(4, 80):
        for x in range(W):
            r = hash01(x, y, 101)
            if r > 0.9968 and math.hypot(x - mx, y - my) > mr + 8:
                bright = hash01(x, y, 102) > 0.8
                c.put(x, y, P["star_hi"] if bright else P["star"])
                if bright and hash01(x, y, 103) > 0.5:
                    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        c.tint(x + dx, y + dy, P["star"], 0.35)


def moon(c: Canvas) -> None:
    mx, my, mr = MOON
    for y in range(my - mr - 1, my + mr + 2):
        for x in range(mx - mr - 1, mx + mr + 2):
            dx, dy = x - mx, y - my
            if dx * dx + dy * dy > mr * mr + 3:
                continue
            # waxing gibbous: terminator curves across the left limb
            half = math.sqrt(max(0, mr * mr - dy * dy))
            if dx < -0.45 * half - 0.5:
                c.put(x, y, mix(P["moon_shadow"], P["sky3"], 0.3))
                continue
            colour = P["moon"]
            n = noise2(x * 0.42, y * 0.42, 7)
            if n > 0.64:
                colour = P["moon_dk"]
            elif n > 0.55:
                colour = P["moon_lo"]
            if dx < -0.45 * half + 1.5 or dx * dx + dy * dy > (mr - 1) ** 2:
                colour = mix(colour, P["moon_lo"], 0.6)
            c.put(x, y, colour)


# --- background layers -------------------------------------------------------
def _shade(c: Canvas, mask: Mask, base, tex, deep, rim, rim_top, seed: int,
           tex_scale=(0.22, 0.45), rim_chance: float = 1.0) -> None:
    for x, y in mask.pixels():
        n = noise2(x * tex_scale[0], y * tex_scale[1], seed)
        colour = tex if n > 0.62 else deep if n < 0.3 else base
        right_edge = not mask(x + 1, y) or not mask(x + 1, y - 1)
        top_edge = not mask(x, y - 1)
        if right_edge and hash01(x, y, seed) < rim_chance:
            colour = rim
        elif top_edge:
            colour = rim_top
        c.put(x, y, colour)


def far_forest(c: Canvas) -> None:
    m = Mask()
    for x in range(W):
        top = int(70 + 9 * fbm1(x * 0.012, 3) - 7 * fbm1(x * 0.045, 4))
        for y in range(top, 112):
            m.set(x, y)
    x = -6
    while x < W + 6:
        h = 5 + int(hash01(x, 0, 5) * 15)
        base = int(70 + 9 * fbm1(x * 0.012, 3) - 7 * fbm1(x * 0.045, 4)) + 2
        tier = 3 + int(hash01(x, 1, 5) * 2)
        for i in range(h):
            hw = int(i * 0.34 * (0.6 + 0.4 * ((i % tier) / tier)))
            m.span(x - hw, x + hw, base - h + i)
        x += 3 + int(hash01(x, 2, 5) * 7)
    _shade(c, m, P["far"], P["far_tex"], P["far"], P["far_rim"], P["far_rim"], 21,
           rim_chance=0.55)


def mist(c: Canvas, y0: int, y1: int, strength: float, seed: int, colour=None) -> None:
    """Horizontal fog streaks in two translucent steps with clean pixel edges."""
    colour = colour or P["mist"]
    for y in range(y0, y1):
        profile = math.sin(math.pi * (y - y0) / (y1 - y0))
        for x in range(W):
            p = profile * strength * fbm2(x * 0.012, y * 0.32, seed) * 2
            if p > 0.62:
                c.tint(x, y, colour, 0.26)
            elif p > 0.4:
                c.tint(x, y, colour, 0.13)


def tower(c: Canvas) -> None:
    x0, x1, base = 62, 82, 104
    m = Mask()
    for x in range(x0, x1 + 1):
        # broken crown: tall on the left, collapsed to the right
        top = 23 + int((x - x0) * 0.9) + int(hash01(x, 0, 41) * 3)
        if x in (x0, x0 + 1, x0 + 4, x0 + 5):
            top = 20 + int(hash01(x, 1, 41) * 2)      # surviving merlons
        for y in range(top, base):
            m.set(x, y)
    for x, y in m.pixels():
        row = (y - 20) // 3
        joint = (x + (4 if row % 2 else 0)) % 7 == 0
        colour = P["tower"]
        if (y - 20) % 3 == 0 or joint:
            colour = P["mortar"]
        if not m(x + 1, y) or not m(x, y - 1):
            colour = P["tower_hi"]
        elif not m(x - 1, y) or x < x0 + 2:
            colour = P["tower_dk"]
        if y > 60 and noise2(x * 0.3, y * 0.15, 43) > 0.58:
            colour = P["mid_tex"]                     # ivy climbing the base
        c.put(x, y, colour)
    # one lit window high up, one dark arrow slit below
    wx, wy = 69, 37
    for y in range(wy - 7, wy + 9):
        for x in range(wx - 8, wx + 10):
            d = math.hypot(x - wx - 0.5, (y - wy - 1) * 1.2)
            if m(x, y) is False and bayer(x, y) < clamp(1 - d / 9) * 0.5:
                c.tint(x, y, P["warm"], 0.5)
    c.rect(wx, wy - 1, 2, 1, P["window"])
    c.rect(wx - 1, wy, 4, 3, P["window"])
    c.rect(wx, wy, 2, 2, P["window_hi"])
    c.put(wx - 1, wy - 1, P["mortar"])
    c.put(wx + 2, wy - 1, P["mortar"])
    c.rect(wx + 4, wy + 18, 1, 4, P["mortar"])


def _fir(m: Mask, cx: int, base: int, height: int, width: float, seed: int) -> None:
    top = base - height
    tier = 6 + int(hash01(seed, 1) * 4)
    lean = (hash01(seed, 2) - 0.5) * 0.08
    for y in range(top, base - 4):
        t = (y - top) / max(1, base - 4 - top)
        phase = ((y - top) % tier) / tier
        hw = 0.6 + t * width * (0.42 + 0.58 * phase ** 0.8)
        hw += (hash01(y, seed, 3) - 0.5) * 1.6
        x = cx + lean * (base - y)
        m.span(round(x - hw), round(x + hw * (0.9 + 0.2 * hash01(y, seed, 4))), y)
    for y in range(base - 5, base + 1):
        m.span(cx - 1, cx + 1, y)


def clumps(c: Canvas, blobs, ramp, seed: int) -> None:
    """Leaf clumps in painter's order, each lit from the upper right.

    ``ramp`` is (shadow, base, lit, moonlit tips). Edges are scalloped so the
    clumps read as foliage rather than circles.
    """
    for k, (cx, cy, r) in enumerate(blobs):
        for y in range(int(cy - r - 2), int(cy + r + 3)):
            for x in range(int(cx - r - 2), int(cx + r + 3)):
                ang = math.atan2(y - cy, x - cx)
                edge = r * (0.8 + 0.3 * noise1(ang * 2.4 + k * 7.3, seed))
                edge += (hash01(x, y, seed + k) - 0.5) * 1.3
                d = math.hypot(x - cx, (y - cy) * 1.12)
                if d > edge:
                    continue
                light = ((x - cx) * 0.55 - (y - cy) * 0.85) / max(r, 1)
                v = light * 0.75 + (noise2(x * 0.5, y * 0.5, seed + 3) - 0.5) * 0.6
                colour = ramp[0] if v < -0.3 else ramp[1] if v < 0.12 else \
                    ramp[2] if v < 0.5 else ramp[3]
                if d > edge - 1.2 and light < 0.1:
                    colour = ramp[0]                       # separates overlapping clumps
                c.put(x, y, colour)


def _broadleaf(c: Canvas, cx: int, base: int, height: int, seed: int) -> None:
    ramp = (P["mid_deep"], P["mid"], P["mid_tex"], P["mid_rim"])
    for y in range(base - height // 2, base + 1):
        c.rect(cx - 1, y, 3, 1, P["mid_deep"])
        c.put(cx + 1, y, P["mid"])
    crown = []
    for k in range(7):
        a = hash01(seed, k, 1) * math.tau
        rr = height * 0.18 * hash01(seed, k, 2)
        crown.append((cx + math.cos(a) * rr * 1.4, base - height * 0.72 + math.sin(a) * rr,
                      height * (0.15 + hash01(seed, k, 3) * 0.1)))
    crown.sort(key=lambda b: b[1])
    clumps(c, crown, ramp, seed)


def _dead_tree(c: Canvas, cx: int, base: int, height: int) -> None:
    trunk, rim = P["mid_deep"], P["mid_rim"]
    for y in range(base - height, base + 1):
        w = 1 + (base - y < height * 0.4) + (base - y < 6)
        x = cx + round(math.sin((base - y) * 0.05) * 2)
        c.rect(x - w + 1, y, w * 2 - 1, 1, trunk)
        c.put(x + w - 1, y, rim)
    for by, dx, length in ((0.75, 1, 11), (0.6, -1, 9), (0.88, -1, 6), (0.45, 1, 7)):
        y0 = base - int(height * by)
        x0 = cx + round(math.sin(int(height * by) * 0.05) * 2)
        for i in range(length):
            x = x0 + dx * i
            y = y0 - int(i * 0.6) - (i * i) // 22
            c.put(x, y, trunk)
            if dx > 0:
                c.put(x, y - 1, rim if i % 3 else trunk)


def mid_forest(c: Canvas) -> None:
    m = Mask()
    x, i = -12, 0
    while x < W + 12:
        i += 1
        if not 50 <= x <= 96:                     # clearing that reveals the tower
            h = 46 + int(hash01(i, 0, 61) * 40)
            if 340 <= x <= 420:
                h -= 16                           # lower behind the arch, opening to the moon
            _fir(m, x, 104 + int(hash01(i, 1, 61) * 4), h, h * (0.19 + hash01(i, 2, 61) * 0.06),
                 seed=i * 13)
        x += 11 + int(hash01(i, 3, 61) * 15)
    _shade(c, m, P["mid"], P["mid_tex"], P["mid_deep"], P["mid_rim"], P["mid_moss"], 63,
           tex_scale=(0.3, 0.55), rim_chance=0.7)
    # a few broadleaf trees and a dead snag break up the rhythm of firs
    _dead_tree(c, 178, 104, 64)
    _broadleaf(c, 128, 106, 58, 64)
    _broadleaf(c, 298, 106, 64, 65)
    _broadleaf(c, 438, 106, 52, 66)


def _bricks(c: Canvas, m: Mask, seed: int, radial=None) -> None:
    for x, y in m.pixels():
        if radial:
            ax, ay, r_in = radial
            ang = math.atan2(ay - y, x - ax)
            joint = int(ang * 9) != int(math.atan2(ay - y, x + 1 - ax) * 9)
            course = False
        else:
            joint = (x + (3 if (y // 4) % 2 else 0)) % 6 == 0
            course = y % 4 == 0
        colour = P["ruin"]
        if joint or course:
            colour = P["ruin_mortar"]
        n = noise2(x * 0.35, y * 0.35, seed)
        if n > 0.7:
            colour = P["ruin_dk"]
        if not m(x, y - 1):
            colour = P["ruin_edge"]
        elif not m(x + 1, y):
            colour = P["ruin_hi"]
        elif not m(x - 1, y):
            colour = P["ruin_dk"]
        moss = noise2(x * 0.18, y * 0.3, seed + 1)
        if moss > 0.6 and (not m(x, y - 1) or not m(x, y - 2) or moss > 0.7):
            colour = P["moss_hi"] if not m(x, y - 1) else P["moss"]
        c.put(x, y, colour)


def ruins(c: Canvas) -> None:
    # broken arch, right of centre
    ax, ay, r_in, r_out = 382, 72, 16, 26
    m = Mask()
    for x in range(ax - r_out, ax + r_out + 1):
        for y in range(ay - r_out, 105):
            d = math.hypot(x - ax, y - ay)
            if y <= ay:
                if not r_in <= d <= r_out:
                    continue
                ang = math.degrees(math.atan2(ay - y, x - ax))
                if 50 < ang < 76 + hash01(x, y, 77) * 8:   # keystone and a few voussoirs gone
                    continue
            elif not (ax - r_out <= x <= ax - r_in or ax + r_in <= x <= ax + r_out):
                continue
            m.set(x, y)
    _bricks(c, m, 81)
    # keystone fallen at the foot of the right pillar
    for x, y, w, h in ((410, 99, 7, 5), (402, 101, 5, 4)):
        bm = Mask()
        for yy in range(y, y + h):
            bm.span(x + (1 if yy == y else 0), x + w - (1 if yy == y else 0), yy)
        _bricks(c, bm, 82)

    # snapped pillar on the left
    pm = Mask()
    for x in range(36, 47):
        top = 74 + int(abs(x - 39) * 1.4) + int(hash01(x, 0, 83) * 3)
        for y in range(top, 105):
            pm.set(x, y)
    _bricks(c, pm, 84)
    for x in range(49, 57):
        for y in range(99 - (1 if 50 < x < 56 else 0), 105):
            pm.set(x, y)
    _bricks(c, pm, 85)


def moonbeams(c: Canvas) -> None:
    """Soft translucent shafts slanting down-left from the canopy gap."""
    beams = ((322, 6, 0.11), (352, 3, 0.08), (262, 9, 0.07), (205, 4, 0.05))
    for y in range(12, 112):
        fade = clamp((y - 12) / 30) * clamp((112 - y) / 40)
        for x in range(W):
            u = x + 0.52 * y
            for centre, half, strength in beams:
                d = abs(u - centre - 0.52 * 60)
                if d < half:
                    core = 1.0 if d < half * 0.5 else 0.55
                    c.tint(x, y, P["beam"], strength * core * round(fade * 3) / 3)


def undergrowth(c: Canvas) -> None:
    m = Mask()
    for x in range(W):
        top = int(94 + 6 * fbm1(x * 0.06, 91) + 3 * noise1(x * 0.31, 92))
        if 360 <= x <= 404:
            top += 3                          # trodden low under the arch
        for y in range(top, 103):
            m.set(x, y)
    _shade(c, m, P["under"], P["under_hi"], P["mid_deep"], P["under_rim"], P["under_rim"], 93,
           tex_scale=(0.4, 0.6), rim_chance=0.45)
    for i, x in enumerate((20, 96, 168, 236, 288, 330, 420)):
        fern = FERNS[i % len(FERNS)]
        c.blit(fern, x, 102 - len(fern), flip=i % 2 == 1)


# --- clearing floor -------------------------------------------------------------
def _ground_light(x: int, y: int) -> float:
    """Moonlit clearing: brightest centre-right, falling off to the edges."""
    dx = (x - 300) / 260
    dy = (y - 150) / 120
    return clamp(1 - math.hypot(dx, dy))


def ground(c: Canvas) -> None:
    ramp = [P["g0"], P["g1"], P["g2"], P["g3"]]
    for y in range(99, H):
        for x in range(W):
            v = 0.55 * fbm2(x * 0.045, y * 0.11, 31) + 0.55 * _ground_light(x, y) - 0.08
            clump = noise2(x * 0.55, y * 0.8, 32)        # mossy clusters, not a checkerboard
            c.put(x, y, dither_pick(ramp, v, x, y, spread=0.8, threshold=clump))
    for i in range(70):                                  # scattered tufts across the clearing
        x, y = int(hash01(i, 0, 34) * W), 116 + int(hash01(i, 1, 34) * (H - 116))
        grass_tuft(c, x, y, i * 0.77, tall=2 + int(hash01(i, 2, 34) * 2))
    for y in range(103, H):
        for x in range(W):
            r = hash01(x, y, 33)
            if r > 0.994:
                c.put(x, y, P["leaf_hi"] if r > 0.998 else P["leaf"])
            elif r < 0.004:
                c.put(x, y, P["pebble"])
                c.put(x + 1, y, P["pebble_hi"])


def path(c: Canvas, occluder: Canvas) -> None:
    ramp = [P["path0"], P["path1"], P["path2"], P["path3"]]
    for x in range(W):
        top = int(101 + 2.5 * noise1(x * 0.07, 51))
        bottom = int(111 + 2 * noise1(x * 0.09, 52))
        for y in range(top, bottom + 1):
            edge = min(y - top, bottom - y)
            v = 0.35 + 0.35 * fbm2(x * 0.08, y * 0.3, 53) + 0.35 * _ground_light(x, y) - (0.3 if edge == 0 else 0)
            c.put(x, y, dither_pick(ramp, v, x, y))
            if hash01(x, y, 54) > 0.985 and edge > 0:
                c.put(x, y, P["pebble_hi"])
                c.put(x - 1, y + 1, P["path0"])
        if hash01(x, 0, 55) > 0.82:
            grass_tuft(c, x, top, x * 0.37, tall=3)
        if hash01(x, 0, 56) > 0.8:
            grass_tuft(occluder, x, bottom + 1, x * 0.71, tall=4 + int(hash01(x, 1, 56) * 3))
    # a mossy boulder at the front edge of the path that the cat passes behind
    _boulder(occluder, 236, 104, 13, 8, 57)


def _boulder(c: Canvas, x: int, y: int, w: int, h: int, seed: int) -> None:
    cx, cy = x + w / 2, y + h / 2
    for yy in range(y, y + h + 1):
        for xx in range(x, x + w + 1):
            nx, ny = (xx - cx) / (w / 2), (yy - cy) / (h / 2)
            d = nx * nx + ny * ny + (hash01(xx, yy, seed) - 0.5) * 0.15
            if d > 1:
                continue
            lit = nx * 0.6 - ny * 0.8
            colour = P["ruin_hi"] if lit > 0.45 else P["ruin"] if lit > -0.2 else P["ruin_dk"]
            if ny < -0.25 and noise2(xx * 0.4, yy * 0.4, seed) > 0.45:
                colour = P["moss_hi"] if lit > 0.2 else P["moss"]
            if d > 0.8 and ny > 0.2:
                colour = P["night"]
            c.put(xx, yy, colour)


# --- ancient trunks and canopy -------------------------------------------------------
def _trunk(c: Canvas, cx: int, w_top: float, w_base: float, base: int, seed: int,
           roots) -> None:
    m = Mask()
    for y in range(0, base + 1):
        t = y / base
        flare = t ** 6
        hw = w_top / 2 + (w_base - w_top) / 2 * flare
        left = cx - hw + (noise1(y * 0.08, seed) - 0.5) * 3
        right = cx + hw + (noise1(y * 0.08, seed + 1) - 0.5) * 3
        m.span(round(left), round(right), y)
    for pts, thick in roots:
        for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
            steps = max(abs(x1 - x0), abs(y1 - y0))
            for i in range(steps + 1):
                x = round(x0 + (x1 - x0) * i / steps)
                y = round(y0 + (y1 - y0) * i / steps)
                for k in range(thick):
                    m.set(x, y + k)
                    m.set(x + 1, y + k)
            thick = max(1, thick - 1)
    ramp = [P["bark0"], P["bark1"], P["bark2"], P["bark3"]]
    for x, y in m.pixels():
        # vertical bark plates separated by dark grooves; brighter towards the moon
        plate = noise2(x * 0.75 + math.sin(y * 0.05) * 0.8, y * 0.025, seed + 2)
        light = clamp((x - (cx - w_top / 2)) / max(1, w_top))
        idx = 0 if plate < 0.36 else min(3, 1 + int(light * 2.4 + (plate - 0.5) * 1.2))
        colour = ramp[idx]
        if not m(x + 1, y):
            colour = P["bark_rim"]                     # moonlit edge
        elif not m(x + 2, y):
            colour = P["bark3"]
        elif not m(x - 1, y):
            colour = P["bark0"]
        if not m(x, y - 1) and y > base - 30:
            colour = P["bark3"]                        # roots catch light on top
        if y > 24 and noise2(x * 0.12, y * 0.08, seed + 3) > 0.7:
            above = noise2(x * 0.12, (y - 1) * 0.08, seed + 3) > 0.7
            colour = P["bark_moss"] if above else P["bark_moss_hi"]   # lit top of each patch
        c.put(x, y, colour)
    # a dark knot hollow with a lit lower lip
    kx, ky = cx + int(w_top * 0.1), 52 + int(hash01(seed, 0) * 14)
    for y in range(ky - 3, ky + 4):
        for x in range(kx - 2, kx + 3):
            if ((x - kx) / 2.4) ** 2 + ((y - ky) / 3.4) ** 2 <= 1 and m(x, y):
                c.put(x, y, P["night"])
    c.hline(kx - 1, kx + 1, ky + 3, P["bark3"])


def trunks(c: Canvas, lay) -> None:
    left_roots = [
        ([(14, 100), (22, 106), (28, 112), (lay.left + 2, 117), (lay.left - 2, 122)], 3),
        ([(6, 102), (4, 112), (1, 120)], 3),
        ([(18, 98), (30, 103), (40, 106)], 2),
    ]
    right_roots = [
        ([(462, 100), (456, 107), (454, 113), (lay.right - 1, 117), (lay.right + 4, 124)], 3),
        ([(474, 102), (478, 114)], 3),
        ([(458, 98), (446, 103), (436, 106)], 2),
    ]
    _trunk(c, 6, 24, 40, 104, 111, left_roots)
    _trunk(c, 472, 22, 36, 104, 121, right_roots)


def canopy(c: Canvas) -> None:
    def depth(x: int) -> float:
        left = max(0.0, 1 - x / 150) ** 1.5 * 42
        right = max(0.0, 1 - (W - x) / 130) ** 1.5 * 36
        return 5 + left + right + 7 * fbm1(x * 0.05, 131)

    for x in range(W):
        for y in range(0, int(depth(x) * 0.55)):
            c.put(x, y, P["canopy0"])
    blobs, x, k = [], -8.0, 0
    while x < W + 8:
        d = depth(int(clamp(x, 0, W - 1)))
        r = 4 + d * 0.22 + hash01(k, 0, 134) * 3
        blobs.append((x, d - r * 0.55 + (hash01(k, 1, 134) - 0.5) * 4, r))
        if d > 22:                                  # heavier, layered growth near trunks
            blobs.append((x + r * 0.6, d * 0.45, r * 1.1))
        x += r * (0.9 + hash01(k, 2, 134) * 0.5)
        k += 1
    blobs.sort(key=lambda b: b[1] + b[2])
    clumps(c, blobs, (P["canopy0"], P["canopy1"], P["canopy2"], P["canopy_rim"]), 135)
    # hanging vines
    for vx, length in ((34, 30), (47, 18), (104, 14), (152, 9), (300, 8), (418, 16), (437, 28), (452, 20)):
        start = int(depth(vx)) - 2
        for i in range(length):
            x = vx + round(math.sin(i * 0.25 + vx) * 0.8)
            y = start + i
            c.put(x, y, P["vine"])
            if i % 3 == 1:
                c.put(x + (1 if (i // 3) % 2 else -1), y, P["vine_hi"] if i < 6 else P["vine_leaf"])


# --- foreground --------------------------------------------------------------------
def _glow(c: Canvas, x: int, y: int, radius: float, colour, strength: float) -> None:
    for yy in range(int(y - radius), int(y + radius) + 1):
        for xx in range(int(x - radius * 1.6), int(x + radius * 1.6) + 1):
            d = math.hypot((xx - x) / 1.6, yy - y) / radius
            if d < 1 and bayer(xx, yy) < (1 - d) ** 1.5 * strength:
                c.tint(xx, yy, colour, 0.35)


def stump(c: Canvas, cx: int, top: int) -> None:
    """An old cut stump: ringed top face in 3/4 view, grooved bark, roots."""
    rx, ry, height = 8, 3, 9
    wood = [hexc("#2e261c"), hexc("#4a3d2c"), hexc("#5d4d37"), hexc("#6f5d42")]
    bark = [P["bark0"], P["bark1"], P["bark2"], P["bark3"]]
    # roots splaying into the moss
    for dx, length, lift in ((-1, 6, 0), (1, 7, 1), (-1, 3, 2)):
        for i in range(length):
            x = cx + dx * (rx - 1 + i)
            y = top + height - 1 + i // 3 - lift // 2
            c.put(x, y, bark[2])
            c.put(x, y + 1, bark[0])
    for y in range(top, top + height + 1):
        flare = 1 if y > top + height - 3 else 0
        for x in range(cx - rx - flare, cx + rx + flare + 1):
            light = (x - cx + rx) / (2 * rx)
            groove = (x + int(hash01(x, 0, 145) * 2)) % 3 == 0
            idx = 0 if groove else min(3, int(light * 3.2))
            if x >= cx + rx - 1 + flare:
                idx = 3
            colour = bark[idx]
            if light < 0.45 and noise2(x * 0.4, y * 0.5, 146) > 0.5:
                colour = P["moss"] if y > top + 1 else P["moss_hi"]
            c.put(x, y, colour)
    for y in range(top - ry, top + ry + 1):
        for x in range(cx - rx, cx + rx + 1):
            d = math.hypot((x - cx) / rx, (y - top) / ry)
            if d > 1:
                continue
            if d > 0.82:
                colour = bark[3] if x > cx else bark[2]
            else:
                ring = int(d * 5 + noise2(x * 0.5, y, 147) * 0.8)
                colour = wood[3 - ring % 2] if (x - cx) - (y - top) > -2 else wood[1 + ring % 2]
            c.put(x, y, colour)
    c.put(cx - 2, top - 1, wood[0])                              # a crack across the rings
    c.put(cx - 1, top, wood[0])
    c.put(cx, top, wood[0])
    c.put(cx + 1, top + 1, wood[0])
    for x in range(cx - rx - 2, cx + rx + 3):
        c.put(x, top + height + 1, P["night"])


def foreground(c: Canvas, lay) -> None:
    top = lay.bottom + 1
    # grass along the outer edge of the courtyard
    for x in range(4, W - 4, 3):
        if lay.left <= x <= lay.right and hash01(x, 0, 151) > 0.35:
            grass_tuft(c, x, top + 1, x * 0.13, tall=2 + int(hash01(x, 1, 151) * 3))
    for y in range(lay.kerb_y + 4, lay.bottom, 5):
        grass_tuft(c, lay.left - 1, y, y * 0.3, tall=2)
        grass_tuft(c, lay.right + 2, y, y * 0.7, tall=2)

    stump(c, 246, 199)
    _boulder(c, 182, 201, 11, 7, 152)
    _boulder(c, 304, 205, 8, 5, 153)
    for x, y, i, flip in ((172, 210, 0, False), (258, 211, 1, True), (290, 212, 1, False),
                          (lay.right - 6, top + 9, 1, False)):
        s = MUSHROOMS[i]
        _glow(c, x + 4, y - 2, 7, hexc("#5f9f92"), 0.55)
        c.blit(s, x, y - len(s), flip=flip)
    for i, (x, y) in enumerate(((198, 214), (268, 213), (316, 215), (10, 214))):
        fern = FERNS[i % 2]
        c.blit(fern, x, y - len(fern), flip=i % 2 == 0)
    for x in range(0, W, 2):
        if hash01(x, 7, 154) > 0.55:
            grass_tuft(c, x, H - 1, x * 0.29, tall=3 + int(hash01(x, 8, 154) * 4))


def corner_foliage(c: Canvas) -> None:
    """Near-black foreground bushes in the bottom corners frame the scene."""
    ramp = (hexc("#030504"), hexc("#08100b"), hexc("#102017"), hexc("#1d3324"))
    left = [(-2, 206, 11), (12, 212, 9), (-4, 190, 8), (26, 216, 7)]
    right = [(482, 204, 12), (468, 213, 9), (484, 188, 7), (452, 217, 6)]
    clumps(c, left, ramp, 161)
    clumps(c, right, ramp, 162)


def vignette(c: Canvas, strength: float = 0.6, skip=None) -> None:
    """Darken towards the frame edges (a smooth tint, not a dither pattern)."""
    for y in range(H):
        for x in range(W):
            if skip and skip(x, y):
                continue
            d = math.hypot((x - W / 2) / (W * 0.6), (y - H * 0.45) / (H * 0.8))
            t = clamp((d - 0.6) / 0.55) * strength
            if t > 0:
                c.tint(x, y, P["night"], t)


# --- overlays ------------------------------------------------------------------------
def lantern_glow() -> Canvas:
    g = Canvas(37, 25)
    cx, cy = 18, 12
    for y in range(g.h):
        for x in range(g.w):
            d = math.hypot((x - cx) / 1.45, y - cy) / 12
            if d < 1 and bayer(x, y) < (1 - d) ** 1.6 * 0.9:
                g.put(x, y, (255, 196, 110, 58 if d > 0.45 else 92))
    return g


def cat_shadow() -> Canvas:
    s = Canvas(24, 3)
    for y in range(3):
        for x in range(24):
            if ((x - 11.5) / 12) ** 2 + ((y - 1) / 1.6) ** 2 < 1:
                s.put(x, y, (2, 4, 3, 120))
    return s


def mist_overlay(width: int) -> Canvas:
    m = Canvas(width, 22)
    for y in range(m.h):
        profile = math.sin(math.pi * y / m.h)
        for x in range(width):
            p = profile * 0.5 * fbm2(x * 0.03, y * 0.2, 171)
            if bayer(x, y) < p:
                m.put(x, y, (*P["mist"], 70))
    return m
