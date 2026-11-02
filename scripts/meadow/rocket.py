"""Hand-drawn rocket, exhaust flame and satellite sprites for the header.

Same conventions as the cat: ASCII art over a named palette, lit from the
upper right (the moon), with a dark selective outline baked into the art.
"""
from __future__ import annotations

from .pixels import Canvas, hexc, sprite

PAL = {
    "K": hexc("#120e0c"),  # outline
    "L": hexc("#e2dfca"),  # moonlit hull
    "B": hexc("#bdb9a3"),  # hull
    "S": hexc("#8c8a78"),  # hull shade
    "D": hexc("#64635a"),  # hull dark
    "R": hexc("#a65a2c"),  # rust paint
    "r": hexc("#6e3a1f"),  # rust shade
    "G": hexc("#caa24c"),  # brass porthole ring
    "g": hexc("#5f8e8a"),  # porthole glass
    "h": hexc("#cfe6df"),  # glass glint
    "N": hexc("#3b3a36"),  # nozzle
    "n": hexc("#26251f"),  # nozzle shade
    "Y": hexc("#ffcf6e"),  # flame
    "y": hexc("#fff3c4"),  # flame core
    "O": hexc("#e8873a"),  # flame edge
    "o": hexc("#a8502a"),  # flame tail
    "P": hexc("#3d5168"),  # solar panel
    "p": hexc("#5f7a96"),  # panel cell (moonlit)
}

ROCKET = sprite("""
......K......
.....KrK.....
.....KRK.....
....KrRRK....
....KrRRK....
...KSBBLLK...
...KSBBLLK...
..KDSBBBLLK..
..KDSBBBLLK..
..KDSGGGLLK..
..KDGghgGLK..
..KDGgggGLK..
..KDSGGGLLK..
..KDSBBBLLK..
..KrrRRRRRK..
..KDSBBBLLK..
..KDSBBBLLK..
..KDSBBBLLK..
..KDSBBBLLK..
..KDSSBBLLK..
..KrrRRRRRK..
.KKDSBBBLLKK.
KrKDSBBBLLKRK
KrKDSBBBLLKRK
KrrKDSBBLKRRK
KrrKKNNNKKRRK
KKK.KnNnK.KKK
....KnnnK....
""", PAL)

FLAMES = [sprite("""
.OYyYO.
.OYyYO.
..OYO..
..OYO..
...O...
...o...
""", PAL), sprite("""
.OYyYO.
OYyyyYO
.OYyYO.
..OYO..
..OoO..
...O...
...o...
""", PAL), sprite("""
.OYyYO.
.OyyYO.
.OYyO..
..OY...
..OO...
..o....
""", PAL)]

SATELLITE = sprite("""
PpP.....PpP
PPPKKGKKPPP
PpP..K..PpP
""", PAL)

PROBE = sprite("""
.PpP.
KKGKK
.PpP.
""", PAL)


def as_canvas(art) -> Canvas:
    c = Canvas(len(art[0]), len(art))
    c.blit(art, 0, 0)
    return c
