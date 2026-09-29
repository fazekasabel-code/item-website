#!/usr/bin/env python3
"""Make transparent versions of the I.T.E.M. logo from the white-background JPEG.

    assets/brand/item-logo.jpg  ->  assets/brand/item-logo.png       (black lettering, for light backgrounds)
                                ->  assets/brand/item-logo-dark.png  (light lettering, for dark backgrounds)

White is turned into transparency ("colour to alpha", as in GIMP), so the logo sits on any
background without a white box. The red and green marks keep their exact colours; in the dark
variant only the neutral (black/grey) lettering is flipped to light. Standard library + macOS `sips`.
"""
import struct
import subprocess
import tempfile
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "assets/brand/item-logo.jpg"
LIGHT_INK = (242, 240, 234)  # lettering colour in the dark variant (matches --ink in dark mode)
BRAND = {"red": (249, 12, 16), "green": (109, 250, 166)}  # sampled from the logo


def read_bmp(path):
    d = path.read_bytes()
    off = struct.unpack("<I", d[10:14])[0]
    w, h = struct.unpack("<ii", d[18:26])
    bpp = struct.unpack("<H", d[28:30])[0] // 8
    row = (w * bpp + 3) // 4 * 4
    rows = []
    for y in range(abs(h)):
        yy = y if h < 0 else abs(h) - 1 - y  # BMP is bottom-up unless height is negative
        line = []
        for x in range(w):
            i = off + yy * row + x * bpp
            b, g, r = d[i], d[i + 1], d[i + 2]
            line.append((r, g, b))
        rows.append(line)
    return w, abs(h), rows


def color_to_alpha(r, g, b):
    c = [r / 255, g / 255, b / 255]
    a = max(1 - v for v in c)
    if a < 0.02:
        return (0, 0, 0, 0)
    out = [max(0.0, min(1.0, (v - (1 - a)) / a)) for v in c]
    return (*(round(v * 255) for v in out), round(a * 255))


def write_png(path, w, h, pixels):
    raw = b"".join(b"\x00" + bytes(v for px in line for v in px) for line in pixels)

    def chunk(tag, data):
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)

    png = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0))
    png += chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b"")
    path.write_bytes(png)


def main():
    with tempfile.TemporaryDirectory() as tmp:
        bmp = Path(tmp) / "logo.bmp"
        subprocess.run(["sips", "-s", "format", "bmp", str(SRC), "--out", str(bmp)], check=True, capture_output=True)
        w, h, rows = read_bmp(bmp)
    light, dark = [], []
    for line in rows:
        l_line, d_line = [], []
        for r, g, b in line:
            px = color_to_alpha(r, g, b)
            l_line.append(px)
            pr, pg, pb, a = px
            neutral = max(pr, pg, pb) - min(pr, pg, pb) < 60
            if not a:
                d_line.append(px)
            elif neutral:
                d_line.append((*LIGHT_INK, a))
            else:
                # Colour-to-alpha turns the light mint into a half-transparent darker green, which looks
                # muddy on dark backgrounds. Use the true brand colour, with coverage relative to it.
                brand = BRAND["green"] if pg > pr else BRAND["red"]
                brand_a = color_to_alpha(*brand)[3]
                d_line.append((*brand, min(255, round(a * 255 / brand_a))))
        light.append(l_line)
        dark.append(d_line)
    write_png(ROOT / "assets/brand/item-logo.png", w, h, light)
    write_png(ROOT / "assets/brand/item-logo-dark.png", w, h, dark)
    print(f"wrote item-logo.png and item-logo-dark.png ({w}×{h})")


if __name__ == "__main__":
    main()
