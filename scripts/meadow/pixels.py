"""A tiny RGBA pixel canvas, deterministic noise, dithering and a PNG encoder.

Everything here is standard-library Python so the generator runs unchanged on
GitHub Actions. Colours are (r, g, b) tuples; canvases store (r, g, b, a).
"""
from __future__ import annotations

import base64
import math
import struct
import zlib

BAYER4 = ((0, 8, 2, 10), (12, 4, 14, 6), (3, 11, 1, 9), (15, 7, 13, 5))


def hexc(value: str) -> tuple[int, int, int]:
    value = value.lstrip("#")
    return int(value[0:2], 16), int(value[2:4], 16), int(value[4:6], 16)


def mix(a, b, t: float):
    return tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(3))


def bayer(x: int, y: int) -> float:
    """Ordered-dither threshold in (0, 1)."""
    return (BAYER4[y & 3][x & 3] + 0.5) / 16


def hash01(x: int, y: int = 0, seed: int = 0) -> float:
    """Stable pseudo-random value in [0, 1) for integer coordinates."""
    h = (x * 374761393 + y * 668265263 + seed * 982451653) & 0xFFFFFFFF
    h = ((h ^ (h >> 13)) * 1274126177) & 0xFFFFFFFF
    return ((h ^ (h >> 16)) & 0xFFFFFF) / 0x1000000


def _smooth(t: float) -> float:
    return t * t * (3 - 2 * t)


def noise1(x: float, seed: int = 0) -> float:
    i = math.floor(x)
    f = _smooth(x - i)
    return hash01(i, 0, seed) * (1 - f) + hash01(i + 1, 0, seed) * f


def noise2(x: float, y: float, seed: int = 0) -> float:
    ix, iy = math.floor(x), math.floor(y)
    fx, fy = _smooth(x - ix), _smooth(y - iy)
    a = hash01(ix, iy, seed) * (1 - fx) + hash01(ix + 1, iy, seed) * fx
    b = hash01(ix, iy + 1, seed) * (1 - fx) + hash01(ix + 1, iy + 1, seed) * fx
    return a * (1 - fy) + b * fy


def fbm1(x: float, seed: int = 0, octaves: int = 3) -> float:
    total, amp, norm = 0.0, 1.0, 0.0
    for o in range(octaves):
        total += noise1(x * (2 ** o), seed + o * 17) * amp
        norm += amp
        amp *= 0.5
    return total / norm


def fbm2(x: float, y: float, seed: int = 0, octaves: int = 3) -> float:
    total, amp, norm = 0.0, 1.0, 0.0
    for o in range(octaves):
        total += noise2(x * (2 ** o), y * (2 ** o), seed + o * 31) * amp
        norm += amp
        amp *= 0.5
    return total / norm


class Canvas:
    def __init__(self, w: int, h: int, fill=None):
        self.w, self.h = w, h
        px = None if fill is None else (*fill[:3], 255)
        self.px = [[px] * w for _ in range(h)]

    # -- primitive access -------------------------------------------------
    def inside(self, x: int, y: int) -> bool:
        return 0 <= x < self.w and 0 <= y < self.h

    def get(self, x: int, y: int):
        if not self.inside(x, y):
            return None
        return self.px[y][x]

    def put(self, x: int, y: int, colour, alpha: int = 255) -> None:
        if colour is None or not self.inside(x, y):
            return
        self.px[y][x] = (colour[0], colour[1], colour[2],
                         colour[3] if len(colour) == 4 else alpha)

    def tint(self, x: int, y: int, colour, t: float) -> None:
        """Blend an opaque pixel towards a colour."""
        cur = self.get(x, y)
        if cur is None:
            return
        self.px[y][x] = (*mix(cur, colour, t), cur[3])

    def rect(self, x: int, y: int, w: int, h: int, colour) -> None:
        for yy in range(y, y + h):
            for xx in range(x, x + w):
                self.put(xx, yy, colour)

    def hline(self, x0: int, x1: int, y: int, colour) -> None:
        for x in range(x0, x1 + 1):
            self.put(x, y, colour)

    def line(self, x0, y0, x1, y1, colour, width: int = 1) -> None:
        steps = max(abs(x1 - x0), abs(y1 - y0), 1)
        for i in range(steps + 1):
            x = round(x0 + (x1 - x0) * i / steps)
            y = round(y0 + (y1 - y0) * i / steps)
            for w in range(width):
                self.put(x, y + w, colour)

    def blit(self, sprite, x: int, y: int, flip: bool = False) -> None:
        for sy, row in enumerate(sprite):
            n = len(row)
            for sx, colour in enumerate(row):
                if colour is not None:
                    self.put(x + (n - 1 - sx if flip else sx), y + sy, colour)

    def paste(self, other: "Canvas", x: int = 0, y: int = 0) -> None:
        for sy in range(other.h):
            for sx in range(other.w):
                c = other.px[sy][sx]
                if c is None or c[3] == 0:
                    continue
                if c[3] == 255:
                    self.put(x + sx, y + sy, c)
                else:
                    self.tint(x + sx, y + sy, c, c[3] / 255)

    # -- encoding ---------------------------------------------------------
    def to_png(self) -> bytes:
        opaque = all(p is not None and p[3] == 255 for row in self.px for p in row)
        raw = bytearray()
        for row in self.px:
            raw.append(0)
            for p in row:
                if p is None:
                    p = (0, 0, 0, 0)
                raw.extend(p[:3] if opaque else p)
        colour_type = 2 if opaque else 6

        def chunk(tag: bytes, data: bytes) -> bytes:
            body = tag + data
            return (struct.pack(">I", len(data)) + body
                    + struct.pack(">I", zlib.crc32(body) & 0xFFFFFFFF))

        header = struct.pack(">IIBBBBB", self.w, self.h, 8, colour_type, 0, 0, 0)
        return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", header)
                + chunk(b"IDAT", zlib.compress(bytes(raw), 9)) + chunk(b"IEND", b""))

    def data_uri(self) -> str:
        return "data:image/png;base64," + base64.b64encode(self.to_png()).decode()


def sprite(art: str, palette: dict) -> list[list]:
    """Turn an ASCII drawing into rows of colours ('.' and ' ' are clear)."""
    rows = [line for line in art.strip("\n").splitlines()]
    width = max(len(r) for r in rows)
    return [[palette.get(ch) if ch not in ". " else None for ch in r.ljust(width)]
            for r in rows]
