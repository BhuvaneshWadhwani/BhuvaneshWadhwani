"""Small SVG helpers shared by the meadow and the profile header."""
from __future__ import annotations

from .pixels import Canvas

# Nearest-neighbour scaling everywhere; the last value a browser understands wins.
PIXEL_STYLE = ('<style>.px{image-rendering:optimizeSpeed;image-rendering:-moz-crisp-edges;'
               'image-rendering:-webkit-optimize-contrast;image-rendering:crisp-edges;'
               'image-rendering:pixelated}</style>')


def img(canvas: Canvas, x: float = 0, y: float = 0, extra: str = "") -> str:
    return (f'<image class="px" x="{x}" y="{y}" width="{canvas.w}" height="{canvas.h}" '
            f'href="{canvas.data_uri()}"{extra}/>')


def animated(element: str, *animations: str) -> str:
    """Put SMIL animation elements inside a self-closing element."""
    tag = element[1:element.index(" ")]
    return element[:-2] + ">" + "".join(animations) + f"</{tag}>"


def discrete(attr: str, values, keys, dur: float, extra: str = "") -> str:
    return (f'<animate attributeName="{attr}" values="{";".join(str(v) for v in values)}" '
            f'keyTimes="{";".join(f"{k:.4f}" for k in keys)}" calcMode="discrete" '
            f'dur="{dur}s" repeatCount="indefinite"{extra}/>')


def cycle(frames: list[Canvas], dur: float, dx: int = 0, dy: int = 0) -> str:
    """Flip-book: show each frame in turn, the first one when SMIL is off."""
    n = len(frames)
    keys = [i / n for i in range(n)]
    return "".join(
        animated(img(f, dx, dy, f' opacity="{1 if i == 0 else 0}"'),
                 discrete("opacity", ["1" if j == i else "0" for j in range(n)], keys, dur))
        for i, f in enumerate(frames))
