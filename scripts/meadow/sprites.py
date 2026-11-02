"""Hand-drawn props and a small pixel font."""
from __future__ import annotations

from .pixels import Canvas, hexc, sprite

# --- 5px pixel font --------------------------------------------------------
_GLYPHS = {
    "A": ".#./#.#/###/#.#/#.#", "B": "##./#.#/##./#.#/##.", "C": ".##/#../#../#../.##",
    "D": "##./#.#/#.#/#.#/##.", "E": "###/#../##./#../###", "F": "###/#../##./#../#..",
    "G": ".##/#../#.#/#.#/.##", "H": "#.#/#.#/###/#.#/#.#", "I": "###/.#./.#./.#./###",
    "J": "..#/..#/..#/#.#/.#.", "K": "#.#/#.#/##./#.#/#.#", "L": "#../#../#../#../###",
    "M": "#...#/##.##/#.#.#/#...#/#...#", "N": "#..#/##.#/#.##/#..#/#..#",
    "O": ".#./#.#/#.#/#.#/.#.", "P": "##./#.#/##./#../#..", "Q": ".#./#.#/#.#/#.#/.##",
    "R": "##./#.#/##./#.#/#.#", "S": ".##/#../.#./..#/##.", "T": "###/.#./.#./.#./.#.",
    "U": "#.#/#.#/#.#/#.#/###", "V": "#.#/#.#/#.#/#.#/.#.",
    "W": "#...#/#...#/#.#.#/##.##/#...#", "X": "#.#/#.#/.#./#.#/#.#",
    "Y": "#.#/#.#/.#./.#./.#.", "Z": "###/..#/.#./#../###",
    "0": "###/#.#/#.#/#.#/###", "1": ".#./##./.#./.#./###", "2": "##./..#/.#./#../###",
    "3": "##./..#/.#./..#/##.", "4": "#.#/#.#/###/..#/..#", "5": "###/#../##./..#/##.",
    "6": ".##/#../###/#.#/###", "7": "###/..#/.#./.#./.#.", "8": "###/#.#/###/#.#/###",
    "9": "###/#.#/###/..#/##.", ",": "./././#/#", ".": "././././#", "-": ".../.../###/.../...",
    "·": "././#/./.", " ": "../../../../..",
}
GLYPHS = {k: v.split("/") for k, v in _GLYPHS.items()}


def text_width(text: str) -> int:
    return sum(len(GLYPHS[ch][0]) + 1 for ch in text.upper()) - 1


def draw_text(c: Canvas, x: int, y: int, text: str, colour, shadow=None) -> int:
    """Draw text, optionally with a 1px drop shadow. Returns the width drawn."""
    cx = x
    for ch in text.upper():
        rows = GLYPHS[ch]
        if shadow is not None:
            for gy, row in enumerate(rows):
                for gx, bit in enumerate(row):
                    if bit == "#":
                        c.put(cx + gx + 1, y + gy + 1, shadow)
        for gy, row in enumerate(rows):
            for gx, bit in enumerate(row):
                if bit == "#":
                    c.put(cx + gx, y + gy, colour)
        cx += len(rows[0]) + 1
    return cx - x - 1


# --- props -----------------------------------------------------------------
FERN_PAL = {"d": hexc("#14241a"), "g": hexc("#22392a"), "l": hexc("#3a5a3c"),
            "m": hexc("#56784a")}

FERNS = [
    sprite("""
.......m.......
....l..lg..m...
...lg..gl..gl..
.mlg..lgg.lgg..
lg..l.lgglg..lm
g..lgllggg..lg.
..lg.lgdgg.lg..
.lg.lgddgdgg.g.
lg..g.ddd..gd..
g......dd....d.
""", FERN_PAL),
    sprite("""
....m......
..l.lg..m..
.lg.gl.lg..
lg..ggllg.m
g.llggdg.lg
.lg.gdggg..
lg..gdd..g.
g...dd.....
""", FERN_PAL),
]

MUSH_PAL = {"M": hexc("#a7d6c2"), "m": hexc("#6aa696"), "k": hexc("#3e6f66"),
            "w": hexc("#c9c2a4"), "s": hexc("#8a8470"), "o": hexc("#e3f4e8")}

MUSHROOMS = [
    sprite("""
..mMMm.....
.mMoMMm....
kmmmmmk.mM.
...ws..mMMm
...ws..kmmk
...ws...ws.
..sws...ws.
""", MUSH_PAL),
    sprite("""
.mMm..
mMoMm.
kmmmk.
..w...
..ws.M
..ws.k
""", MUSH_PAL),
]

GRASS_DARK = hexc("#1b2a1d")
GRASS_MID = hexc("#2b4229")
GRASS_LIGHT = hexc("#466338")


def grass_tuft(c: Canvas, x: int, y: int, seed: float, tall: int = 4,
               light=GRASS_LIGHT) -> None:
    """Three to five blades leaning slightly, lit at their tips."""
    from .pixels import hash01
    blades = 3 + int(hash01(int(seed * 1000), 3) * 3)
    for b in range(blades):
        bx = x + b - blades // 2
        h = max(2, tall - abs(b - blades // 2) + int(hash01(int(seed * 999), b) * 2))
        lean = (b - blades // 2) / max(1, blades)
        for i in range(h):
            px = bx + round(lean * i)
            colour = light if i == h - 1 else GRASS_MID if i > h // 2 else GRASS_DARK
            c.put(px, y - i, colour)
