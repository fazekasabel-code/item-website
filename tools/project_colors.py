#!/usr/bin/env python3
"""Derive each project's colour from its own logo (or cover) and write it into meta.json.

    python3 tools/project_colors.py           show what would change
    python3 tools/project_colors.py --write   update content/projects/*/meta.json

The colour is the most common saturated colour in the image (black, white and greys are
ignored), so a project's band, hero and index bar carry its own brand, not the I.T.E.M. palette.
Projects whose image has no saturated colour (e.g. a black-only logo) or no image at all get
"color": null and fall back to the neutral ink colour. Run it again when a logo is added or changed.
Standard library + macOS `sips`.
"""
import argparse
import colorsys
import json
import struct
import subprocess
import tempfile
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MIN_SHARE = 0.02  # a colour must cover at least 2 % of the non-background pixels to count as the brand colour


def pixels(image):
    with tempfile.TemporaryDirectory() as tmp:
        bmp = Path(tmp) / "x.bmp"
        subprocess.run(["sips", "-s", "format", "bmp", str(image), "--out", str(bmp)], check=True, capture_output=True)
        d = bmp.read_bytes()
    off = struct.unpack("<I", d[10:14])[0]
    w, h = struct.unpack("<ii", d[18:26])
    bpp = struct.unpack("<H", d[28:30])[0] // 8
    row = (w * bpp + 3) // 4 * 4
    for y in range(abs(h)):
        for x in range(w):
            i = off + y * row + x * bpp
            b, g, r = d[i], d[i + 1], d[i + 2]
            if bpp == 4 and d[i + 3] < 128:
                continue  # transparent
            yield r, g, b


def brand_color(image):
    counts, total = Counter(), 0
    for r, g, b in pixels(image):
        h, l, s = colorsys.rgb_to_hls(r / 255, g / 255, b / 255)
        if l > 0.94:
            continue  # background white
        total += 1
        if s < 0.25 or l < 0.12 or l > 0.88:
            continue  # black, grey, near-white: not a brand colour
        counts[(round(h * 36) % 36)] += 1  # 10° hue buckets
    if not counts or counts.most_common(1)[0][1] < MIN_SHARE * max(total, 1):
        return None
    bucket = counts.most_common(1)[0][0]
    # Average the actual pixels of the winning hue bucket, weighting saturated ones.
    rs = gs = bs = n = 0
    for r, g, b in pixels(image):
        h, l, s = colorsys.rgb_to_hls(r / 255, g / 255, b / 255)
        if l > 0.94 or s < 0.25 or l < 0.12 or l > 0.88 or round(h * 36) % 36 != bucket:
            continue
        rs, gs, bs, n = rs + r * s, gs + g * s, bs + b * s, n + s
    return "#%02x%02x%02x" % (round(rs / n), round(gs / n), round(bs / n))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()
    for folder in sorted((ROOT / "content/projects").iterdir()):
        meta_path = folder / "meta.json"
        if not meta_path.exists():
            continue
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        image = next((folder / meta[k] for k in ("logo", "cover") if meta.get(k)), None)
        color = brand_color(image) if image else None
        source = image.name if image else "no image"
        print(f"{folder.name:45} {str(meta.get('color')):9} -> {str(color):9} ({source})")
        if args.write and color != meta.get("color"):
            meta["color"] = color
            meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
