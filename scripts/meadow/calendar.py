"""The contribution calendar as an overgrown flagstone courtyard.

Each day is one flagstone seen in a 3/4 RPG view: a five-pixel top face and a
two-pixel front lip. Contribution level drives the moss on the top face, from
bare slate (0) to thick luminous moss (4), so the five levels read as a clear
value ladder even at small sizes.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from .pixels import Canvas, hash01, hexc, mix
from .sprites import draw_text, text_width

PITCH = 8              # stone 7px + 1px grout, both axes
STONE_W, TOP_H, FRONT_H = 7, 5, 2

# top, top highlight, top shadow, front, front shadow, texture accent
LEVELS = {
    0: ("#262d31", "#323b40", "#1f2528", "#171c1f", "#111518", "#1b2124"),
    1: ("#2f5532", "#3d6a3b", "#284a2b", "#1d3320", "#162819", "#4b7a42"),
    2: ("#44773a", "#589046", "#3a6633", "#2a4a25", "#1f381c", "#6fa552"),
    3: ("#66a03f", "#80b84d", "#578c35", "#3f6627", "#2f4e1e", "#9cca63"),
    4: ("#a1cc5c", "#c0e07e", "#8ab64c", "#62903a", "#4b712c", "#eaf5c4"),
}
LEVELS = {k: tuple(hexc(c) for c in v) for k, v in LEVELS.items()}
# Bare slabs vary in hue (blue slate, green slate, warm grey) at the same value,
# so the floor looks quarried rather than tiled without blurring level 0.
SLATE = [tuple(hexc(c) for c in v) for v in (
    ("#262d31", "#323b40", "#1f2528"),
    ("#272e2b", "#333c37", "#202623"),
    ("#2b2c2d", "#383a3a", "#232425"),
)]

GROUT = hexc("#090c0b")
GROUT_GRASS = hexc("#1d2d1c")
KERB_TOP, KERB_HL, KERB_SHADE = hexc("#353c3a"), hexc("#48504c"), hexc("#2a302f")
KERB_FRONT, KERB_FRONT_DK = hexc("#1f2423"), hexc("#151918")
KERB_MOSS, KERB_MOSS_HL = hexc("#30452b"), hexc("#46613a")
MONTH, MONTH_SHADOW = hexc("#a9b29c"), hexc("#151918")
EARTH, EARTH_DK = hexc("#161511"), hexc("#0f0e0b")


@dataclass
class Layout:
    weeks: int
    gx: int            # x of the first stone column
    gy: int = 124      # y of the first stone row's top face
    kerb_y: int = 115  # top of the back kerb

    @property
    def grid_w(self) -> int:
        return self.weeks * PITCH - 1

    @property
    def grid_bottom(self) -> int:  # last grout row
        return self.gy + 7 * PITCH - 1

    @property
    def left(self) -> int:         # outer edge of the left kerb
        return self.gx - 5

    @property
    def right(self) -> int:        # outer edge of the right kerb
        return self.gx + self.grid_w + 4

    @property
    def front_kerb_y(self) -> int:
        return self.grid_bottom + 1

    @property
    def bottom(self) -> int:       # last row of the front kerb lip
        return self.front_kerb_y + 5

    def cell(self, col: int, row: int) -> tuple[int, int]:
        return self.gx + col * PITCH, self.gy + row * PITCH


def make_layout(weeks: int, width: int) -> Layout:
    return Layout(weeks=weeks, gx=(width - (weeks * PITCH - 1)) // 2)


def arrange(days: list[dict]) -> list:
    """Pad GraphQL days into Sunday-first columns (None = outside the range)."""
    first = (date.fromisoformat(days[0]["date"]).weekday() + 1) % 7
    cells = [None] * first + list(days)
    while len(cells) % 7:
        cells.append(None)
    return cells


def stone(c: Canvas, x: int, y: int, level: int, seed: int) -> None:
    top, hl, dk, front, fdk, accent = LEVELS[level]
    r = lambda i: hash01(seed, i, 71)
    if level == 0:
        top, hl, dk = SLATE[int(r(0) * len(SLATE))]
    for yy in range(TOP_H):
        for xx in range(STONE_W):
            if yy == 0 and xx in (0, STONE_W - 1):
                continue                                 # rounded back corners
            colour = top
            if yy == 0 or (xx == STONE_W - 1 and yy < 3):
                colour = hl                              # moonlit rim (light from upper right)
            elif (xx == 0 and yy >= 3) or (xx == 1 and yy == 4):
                colour = dk
            c.put(x + xx, y + yy, colour)
    for xx in range(STONE_W):
        c.put(x + xx, y + TOP_H, front)
        if 0 < xx < STONE_W - 1:
            c.put(x + xx, y + TOP_H + 1, fdk)

    # surface texture, unique per stone but never strong enough to blur levels
    if level == 0:
        cx, cy = 1 + int(r(1) * 4), 1 + int(r(2) * 2)
        c.put(x + cx, y + cy, accent)
        c.put(x + cx + 1, y + cy + 1, accent)
        if r(3) > 0.5:
            c.put(x + cx + 2, y + cy + 1, accent)
        if r(4) > 0.7:                                    # pale lichen fleck
            c.put(x + 1 + int(r(5) * 5), y + 1 + int(r(6) * 3), mix(top, hexc("#5d6b62"), 0.5))
    else:
        for i in range(2 + level // 2):
            c.put(x + 1 + int(r(10 + i) * 5), y + 1 + int(r(20 + i) * 3), accent)
        c.put(x + 1 + int(r(30) * 5), y + 1 + int(r(31) * 3), dk)
        if level >= 2 and r(32) > 0.35:                   # moss creeping over the lip
            c.put(x + 1 + int(r(33) * 5), y + TOP_H, mix(front, top, 0.6))
        if level == 4:
            c.put(x + 2 + int(r(40) * 3), y + 1 + int(r(41) * 2), hexc("#f6fbe0"))


def _kerb_run(c: Canvas, x0: int, x1: int, y: int, top_rows: int, seed: int) -> None:
    """Kerb top face plus a two-pixel front face, with wear and moss."""
    joint = x0 + 3 + int(hash01(x0, y, seed) * 8)
    for x in range(x0, x1 + 1):
        if x == joint:                                   # uneven block joints
            joint += 9 + int(hash01(x, y, seed) * 7)
            for yy in range(top_rows + 2):
                c.put(x, y + yy, KERB_FRONT_DK)
            continue
        for yy in range(top_rows):
            colour = KERB_HL if yy == 0 else KERB_SHADE if yy == top_rows - 1 else KERB_TOP
            c.put(x, y + yy, colour)
        c.put(x, y + top_rows, KERB_FRONT)
        c.put(x, y + top_rows + 1, KERB_FRONT_DK)
        if hash01(x, y, seed + 1) > 0.94 and x + 1 <= x1:   # small chips off the top edge
            c.put(x, y, KERB_SHADE)
            c.put(x + 1, y, KERB_FRONT)


def _kerb_moss(c: Canvas, x0: int, x1: int, y: int, rows: int, seed: int, avoid=()) -> None:
    """Moss cushions on the kerb, draping over its front lip where thick."""
    from .pixels import noise1
    for x in range(x0, x1 + 1):
        if any(a <= x <= b for a, b in avoid):
            continue
        n = noise1(x * 0.12, seed)
        if n > 0.6:
            depth = 1 + int((n - 0.6) * 14)
            for yy in range(min(depth, rows + 2)):
                c.put(x, y + yy, KERB_MOSS_HL if yy == 0 else KERB_MOSS)
            if depth > rows and hash01(x, y, seed) > 0.4:  # drips over the lip
                c.put(x, y + rows + 2, KERB_MOSS)


def month_labels(cells: list, lay: Layout) -> list[tuple[int, str]]:
    labels, last_x, last_month = [], -99, None
    for col in range(lay.weeks):
        days = [d for d in cells[col * 7:col * 7 + 7] if d]
        if not days:
            continue
        d0 = date.fromisoformat(days[0]["date"])
        month = d0.strftime("%b").upper()
        if month == last_month:
            continue
        if d0.day > 7 and labels:
            continue
        x = lay.cell(col, 0)[0]
        if x - last_x < 16 or x + text_width(month) > lay.gx + lay.grid_w:
            last_month = month
            continue
        labels.append((x, month))
        last_x, last_month = x, month
    return labels


def draw_courtyard(c: Canvas, cells: list, lay: Layout) -> list[dict]:
    """Draw kerbs, grout and all stones. Returns tile boxes for tooltips."""
    # grout bed
    c.rect(lay.gx - 1, lay.kerb_y + 8, lay.grid_w + 2, lay.grid_bottom - lay.kerb_y - 7, GROUT)

    # back kerb with carved month names
    labels = month_labels(cells, lay)
    spans = [(x - 2, x + text_width(m) + 2) for x, m in labels]
    _kerb_run(c, lay.left, lay.right, lay.kerb_y, 6, 11)
    _kerb_moss(c, lay.left, lay.right, lay.kerb_y, 4, 12, avoid=spans)
    for x, month in labels:
        draw_text(c, x, lay.kerb_y + 1, month, MONTH, shadow=MONTH_SHADOW)
    # grass leaning over the back kerb from the path verge
    from .sprites import grass_tuft
    for x in range(lay.left, lay.right, 4):
        if hash01(x, 1, 13) > 0.45 and not any(a - 2 <= x <= b + 2 for a, b in spans):
            grass_tuft(c, x, lay.kerb_y + 1, x * 0.17, tall=2 + int(hash01(x, 2, 13) * 2))

    # side kerbs (top faces only; their ends tuck under the front kerb)
    for x0 in (lay.left, lay.gx + lay.grid_w + 1):
        for y in range(lay.kerb_y + 6, lay.front_kerb_y):
            for xx in range(4):
                colour = KERB_HL if (x0 > lay.gx and xx == 0) else \
                    KERB_SHADE if xx == 3 or hash01(x0 + xx, y, 5) > 0.9 else KERB_TOP
                c.put(x0 + xx, y, colour)
            if (y - lay.kerb_y) % 13 == 0:
                c.hline(x0, x0 + 3, y, KERB_FRONT_DK)

    # front kerb
    _kerb_run(c, lay.left, lay.right, lay.front_kerb_y, 4, 21)
    _kerb_moss(c, lay.left, lay.right, lay.front_kerb_y, 3, 22)

    tiles = []
    for idx, day in enumerate(cells):
        col, row = divmod(idx, 7)
        x, y = lay.cell(col, row)
        if day is None:
            # outside the year: bare earth with a crumb of old stone
            c.rect(x, y, STONE_W, TOP_H + FRONT_H, EARTH)
            c.put(x + 2 + int(hash01(col, row, 9) * 3), y + 3, EARTH_DK)
            continue
        if hash01(col, row, 3) > 0.9:                  # weeds in the grout
            c.put(x + STONE_W, y + 2 + int(hash01(col, row, 4) * 4), GROUT_GRASS)
        stone(c, x, y, day["level"], seed=col * 7 + row)
        tiles.append({**day, "x": x, "y": y})
    return tiles


def draw_day_labels(c: Canvas, lay: Layout, colour, shadow) -> None:
    for row, name in ((1, "MON"), (3, "WED"), (5, "FRI")):
        y = lay.cell(0, row)[1] + 1
        draw_text(c, lay.left - 2 - text_width(name), y, name, colour, shadow=shadow)


def draw_legend(c: Canvas, x: int, y: int, colour, shadow) -> int:
    """'LESS [0][1][2][3][4] MORE' using the real flagstones."""
    cx = x + draw_text(c, x, y + 1, "LESS", colour, shadow=shadow) + 4
    for level in range(5):
        c.rect(cx - 1, y - 1, STONE_W + 2, TOP_H + FRONT_H + 2, GROUT)
        stone(c, cx, y, level, seed=level * 13 + 5)
        cx += PITCH + 1
    cx += 3
    cx += draw_text(c, cx, y + 1, "MORE", colour, shadow=shadow)
    return cx - x
