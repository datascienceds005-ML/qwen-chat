#!/usr/bin/env python3
"""Generate PWA icons with ZERO dependencies (stdlib PNG encoder).
Run once, commit the PNGs. Bubble sits inside the maskable safe zone."""
import struct
import zlib
from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / "frontend" / "icons"
BG, GREEN = (14, 16, 19), (52, 199, 123)


def _in_rounded(x, y, cx, cy, hw, hh, r):
    dx, dy = abs(x - cx) - (hw - r), abs(y - cy) - (hh - r)
    if dx > 0 and dy > 0:
        return dx * dx + dy * dy <= r * r
    return abs(x - cx) <= hw and abs(y - cy) <= hh


def _pixel_fn(size):
    s = size
    pad = 0.17 * s
    bx0, by0, bx1, by1 = pad, 0.20 * s, s - pad, 0.74 * s
    cx, cy = (bx0 + bx1) / 2, (by0 + by1) / 2
    hw, hh, r = (bx1 - bx0) / 2, (by1 - by0) / 2, 0.10 * s
    tcx, tcy, tr = bx0 + 0.12 * s, by1, 0.085 * s
    dot_r, dots = 0.045 * s, (0.38 * s, 0.50 * s, 0.62 * s)

    def px(x, y):
        for d in dots:
            ddx, ddy = x - d, y - cy
            if ddx * ddx + ddy * ddy <= dot_r * dot_r:
                return BG
        if _in_rounded(x, y, cx, cy, hw, hh, r):
            return GREEN
        ddx, ddy = x - tcx, y - tcy
        if y >= tcy and ddx * ddx + ddy * ddy <= tr * tr:
            return GREEN
        return BG

    return px


def write_png(size: int) -> bytes:
    px = _pixel_fn(size)
    raw = b"".join(
        b"\x00" + b"".join(bytes(px(x, y)) for x in range(size))
        for y in range(size)
    )

    def chunk(tag: bytes, data: bytes) -> bytes:
        return (struct.pack(">I", len(data)) + tag + data
                + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF))

    ihdr = struct.pack(">IIBBBBB", size, size, 8, 2, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", ihdr)
            + chunk(b"IDAT", zlib.compress(raw, 9))
            + chunk(b"IEND", b""))


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for size in (192, 512):
        path = OUT / f"icon-{size}.png"
        path.write_bytes(write_png(size))
        print(f"wrote {path}")


if __name__ == "__main__":
    main()
