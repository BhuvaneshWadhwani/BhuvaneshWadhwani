"""The orange explorer cat: hand-drawn torso plus generated legs and tail.

The head, cloak, pack and lantern are drawn by hand below. Legs and tail are
posed per frame so the four-frame walk cycle stays consistent, and a dark
selective outline is added around the finished silhouette.
"""
from __future__ import annotations

from .pixels import Canvas, hexc, sprite

W, H = 30, 20          # frame size; paws rest on row H - 1
GROUND = H - 1

PAL = {
    "K": hexc("#1c120d"),  # outline
    "O": hexc("#d4802e"),  # fur
    "L": hexc("#f0a64e"),  # moonlit fur
    "D": hexc("#9a5021"),  # fur shadow
    "S": hexc("#7a3a15"),  # tabby stripe
    "W": hexc("#f1d7aa"),  # muzzle / chest
    "P": hexc("#c77a68"),  # inner ear
    "N": hexc("#d98a7e"),  # nose
    "E": hexc("#e8d46a"),  # eye shine
    "C": hexc("#3f5040"),  # cloak
    "c": hexc("#2c382d"),  # cloak shadow
    "H": hexc("#62755e"),  # cloak moonlit edge
    "B": hexc("#6e4a2b"),  # pack leather
    "b": hexc("#4b301b"),  # pack dark
    "G": hexc("#caa24c"),  # brass
    "R": hexc("#8d7c58"),  # bedroll
    "r": hexc("#665838"),  # bedroll shadow
    "F": hexc("#2f2a24"),  # lantern frame
    "Y": hexc("#ffcf6e"),  # lantern glass
    "y": hexc("#fff3c4"),  # lantern core
}

# Torso, head, pack and lantern (no legs, no tail). Facing right.
TORSO = """
..............................
..............................
....................K....K....
.......KRRrRRrRK..KLK..KLK....
.......KrrbrrbrK..KPOKKOPK....
........KBBBBBK...KOOOOLLLK...
....KKKKKBbGbBKKKKSOSOOOOLK...
...KOHHHKBBBBBKHCKOOOOOEKOOK..
..KOOCCCKBBbBBKCGKOOOOOOOWWN..
..KODCCCKKKKKKKCCCKOOOOOWWWK..
..KDDcCCCCCCCCCCCCCKDOWWWKK...
..KSOcCCCCCCCCCCCccKKKKK......
..KDOccCccCcccCccOOWK.F.......
..KDDKcKccKcKccKOOWWKFYF......
...KDODSOOSOOSOOOWWOKYyY......
....KKKKKKKKKKKKKKKK.FFF......
"""

# Leg roots (x at the hip) and per-frame foot offsets: near/far, back/front.
LEGS = (("far", 5), ("near", 7), ("far", 16), ("near", 18))
STRIDE = (
    (-2, 2, 2, -2),
    (0, 0, 0, 0),
    (2, -2, -2, 2),
    (0, 0, 0, 0),
)
BOB = (0, -1, 0, -1)

# Tail centre lines from the rump upward; three sway poses.
TAILS = {
    -1: ((3, 9), (2, 8), (1, 7), (1, 6), (1, 5), (1, 4), (2, 3), (3, 2)),
    0: ((3, 9), (2, 8), (1, 7), (1, 6), (1, 5), (2, 4), (3, 3), (4, 3)),
    1: ((3, 9), (2, 8), (2, 7), (2, 6), (2, 5), (3, 4), (4, 4), (5, 3)),
}


def _draw_tail(c: Canvas, pose: int, dy: int) -> None:
    pts = TAILS[pose]
    for i, (x, y) in enumerate(pts):
        stripe = i in (2, 4, 6)
        c.put(x, y + dy, PAL["S"] if stripe else PAL["O"])
        c.put(x + 1, y + dy, PAL["D"] if stripe else PAL["L"] if i > 2 else PAL["O"])


def _draw_leg(c: Canvas, hip: int, dx: int, near: bool, top: int) -> None:
    fur, shade = (PAL["O"], PAL["D"]) if near else (PAL["D"], PAL["S"])
    rows = GROUND - top
    for i in range(rows):
        x = hip + round(dx * (i + 1) / rows)
        c.put(x, top + i, shade)
        c.put(x + 1, top + i, fur)
    foot = hip + dx
    c.put(foot, GROUND, PAL["K"])
    c.put(foot + 1, GROUND, PAL["W"] if near else PAL["D"])
    c.put(foot + 2, GROUND, PAL["K"])


def _outline(c: Canvas) -> None:
    filled = {(x, y) for y in range(c.h) for x in range(c.w) if c.get(x, y)}
    for x, y in list(filled):
        for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if c.inside(nx, ny) and (nx, ny) not in filled and ny < GROUND:
                c.put(nx, ny, PAL["K"])


def frame(step: int, tail: int = 0, still: bool = False) -> Canvas:
    """One walk frame (step 0-3). Passing frames lift the body by a pixel.

    With ``still`` the cat stands square on all four paws (idle pose).
    """
    c = Canvas(W, H)
    dy = 0 if still else BOB[step]
    stride = (0, 0, 0, 0) if still else STRIDE[step]
    torso = sprite(TORSO, PAL)
    belly = len(torso) - 1 + dy
    # far legs first, torso over them, near legs on top
    for (depth, hip), dx in zip(LEGS, stride):
        if depth == "far":
            _draw_leg(c, hip, dx, False, belly)
    c.blit(torso, 0, dy)
    for (depth, hip), dx in zip(LEGS, stride):
        if depth == "near":
            _draw_leg(c, hip, dx, True, belly)
    _draw_tail(c, tail, dy)
    _outline(c)
    return c


def flipped(c: Canvas) -> Canvas:
    out = Canvas(c.w, c.h)
    for y in range(c.h):
        out.px[y] = list(reversed(c.px[y]))
    return out
