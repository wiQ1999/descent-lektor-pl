"""Rasteryzuje logo SVG (ścieżki M/L/H/V/C/S/Z, fill-rule evenodd) do PNG bez zewnętrznych rasteryzatorów.

Ikona przycisku „PL” w nakładce (E18) to biały wariant w 128 px, osadzony w LektorPL.Core.dll:

    .venv/Scripts/python -I analysis/tools/logo_png.py assets/logo/lektor-pl-bialy.svg src/plugin/Core/Resources/logo-bialy.png --size 128
"""
from __future__ import annotations

import argparse
import re
import xml.etree.ElementTree as ET
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw

SS = 8  # nadpróbkowanie do wygładzania krawędzi
TOKEN = re.compile(r"[MLHVCSZmlhvcsz]|-?\d*\.?\d+(?:e-?\d+)?")


def _cubic(p0, p1, p2, p3, steps=24):
    out = []
    for i in range(1, steps + 1):
        t = i / steps
        u = 1 - t
        out.append((
            u**3 * p0[0] + 3 * u * u * t * p1[0] + 3 * u * t * t * p2[0] + t**3 * p3[0],
            u**3 * p0[1] + 3 * u * u * t * p1[1] + 3 * u * t * t * p2[1] + t**3 * p3[1],
        ))
    return out


def subpaths(d: str) -> list[list[tuple[float, float]]]:
    """Zamienia atrybut d na listę wielokątów (krzywe spłaszczone)."""
    toks = TOKEN.findall(d)
    paths, cur, pos, start, last_ctrl, cmd, i = [], [], (0.0, 0.0), (0.0, 0.0), None, None, 0

    def num():
        nonlocal i
        i += 1
        return float(toks[i - 1])

    while i < len(toks):
        if toks[i].isalpha():
            cmd = toks[i]
            i += 1
            if cmd in "Zz":
                if cur:
                    paths.append(cur)
                cur, pos, last_ctrl = [], start, None
                continue
        rel = cmd.islower()
        ox, oy = pos if rel else (0.0, 0.0)
        c = cmd.upper()
        if c == "M":
            if cur:
                paths.append(cur)
            pos = start = (ox + num(), oy + num())
            cur = [pos]
            cmd = "l" if rel else "L"
            last_ctrl = None
        elif c == "L":
            pos = (ox + num(), oy + num())
            cur.append(pos)
            last_ctrl = None
        elif c == "H":
            pos = ((pos[0] if rel else 0.0) + num(), pos[1])
            cur.append(pos)
            last_ctrl = None
        elif c == "V":
            pos = (pos[0], (pos[1] if rel else 0.0) + num())
            cur.append(pos)
            last_ctrl = None
        elif c in "CS":
            if c == "C":
                p1 = (ox + num(), oy + num())
            else:
                p1 = (2 * pos[0] - last_ctrl[0], 2 * pos[1] - last_ctrl[1]) if last_ctrl else pos
            p2 = (ox + num(), oy + num())
            p3 = (ox + num(), oy + num())
            cur.extend(_cubic(pos, p1, p2, p3))
            pos, last_ctrl = p3, p2
        else:
            raise ValueError(f"nieobsługiwane polecenie ścieżki: {cmd}")
    if cur:
        paths.append(cur)
    return paths


def render(svg: Path, size: int) -> Image.Image:
    root = ET.parse(svg).getroot()
    vb = [float(v) for v in root.get("viewBox").split()]
    big = size * SS
    sx, sy = big / vb[2], big / vb[3]
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    for el in root.iter("{http://www.w3.org/2000/svg}path"):
        mask = Image.new("L", (big, big), 0)
        for poly in subpaths(el.get("d")):  # evenodd: XOR kolejnych podścieżek (niezerowe też tu wystarcza)
            one = Image.new("L", (big, big), 0)
            ImageDraw.Draw(one).polygon([((x - vb[0]) * sx, (y - vb[1]) * sy) for x, y in poly], fill=255)
            mask = ImageChops.logical_xor(mask.convert("1"), one.convert("1")).convert("L")
        mask = mask.resize((size, size), Image.LANCZOS)
        fill = el.get("fill", "#000000").lstrip("#")
        color = tuple(int(fill[k:k + 2], 16) for k in (0, 2, 4))
        layer = Image.new("RGBA", (size, size), color + (0,))
        layer.putalpha(mask)
        img = Image.alpha_composite(img, layer)
    return img


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("svg", type=Path)
    ap.add_argument("png", type=Path)
    ap.add_argument("--size", type=int, default=128)
    a = ap.parse_args()
    a.png.parent.mkdir(parents=True, exist_ok=True)
    render(a.svg, a.size).save(a.png, optimize=True)
    print(f"{a.png} {a.size}x{a.size}")


if __name__ == "__main__":
    main()
