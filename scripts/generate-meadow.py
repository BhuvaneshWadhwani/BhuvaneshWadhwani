#!/usr/bin/env python3
"""Build an animated, dark-fantasy pixel-art GitHub contribution meadow.

Reads the contribution calendar from GitHub GraphQL and writes:
    dist/contribution-meadow.svg

Uses only Python's standard library. Set GITHUB_TOKEN in the environment.
For offline previews, pass --from-json with a file shaped like
{"total": 123, "days": [{"date": "2025-11-02", "count": 0, "level": 0}, ...]}.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from meadow.github import fetch_calendar
from meadow.render import build_svg

USERNAME = "BhuvaneshWadhwani"
OUTPUT = Path("dist/contribution-meadow.svg")


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--from-json", type=Path,
                        help="render from a saved calendar instead of calling GitHub")
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()

    if args.from_json:
        data = json.loads(args.from_json.read_text(encoding="utf-8"))
        days, total = data["days"], int(data["total"])
    else:
        days, total = fetch_calendar(USERNAME)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(build_svg(days, total), encoding="utf-8")
    print(f"Wrote {args.output} ({len(days)} days, {total} contributions).")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
