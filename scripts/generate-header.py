#!/usr/bin/env python3
"""Render the profile header in the same pixel-art world as the meadow.

Writes assets/title.svg and assets/rocket-retro.svg. Neither depends on
contribution data, so this is run by hand and the output is committed.
"""
from __future__ import annotations

from pathlib import Path

from meadow.header import rocket_svg, title_svg

ASSETS = Path(__file__).resolve().parent.parent / "assets"


def main():
    for name, svg in (("title.svg", title_svg()), ("rocket-retro.svg", rocket_svg())):
        path = ASSETS / name
        path.write_text(svg, encoding="utf-8")
        print(f"Wrote {path} ({len(svg) // 1024} KB)")


if __name__ == "__main__":
    main()
