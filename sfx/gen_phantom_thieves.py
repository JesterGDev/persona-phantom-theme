#!/usr/bin/env python3
"""Phantom Thieves wallpapers -- Persona 5 only: black, white, one red, gold.

Four designs, all built from the game's own visual language: jagged red slashes,
the signature diagonal bars, a domino mask, and a comic impact burst. Screentone
halftone throughout, because Persona 5's UI is drawn like a manga panel.
"""

import math
import os
import sys
import time

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

W, H = 2560, 1440
OUT = os.path.expanduser("~/.config/omarchy/themes/phantom-thieves/backgrounds")

BLACK = (0x0A / 255, 0x0A / 255, 0x0A / 255)
RED = (0xE6 / 255, 0x00 / 255, 0x12 / 255)
PINK = (0xFF / 255, 0x5C / 255, 0x8A / 255)
GOLD = (0xFF / 255, 0xC7 / 255, 0x2C / 255)
WHITE = (1.0, 1.0, 1.0)

SS = 2
_GRID = None


def coord_grid():
    global _GRID
    if _GRID is None:
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        _GRID = (xx / W, yy / H)
    return _GRID


def canvas(fill=BLACK):
    return np.empty((H, W, 3), dtype=float) + np.array(fill, dtype=float)


def linear_gradient(c0, c1, angle_deg):
    xx, yy = coord_grid()
    a = math.radians(angle_deg)
    t = xx * math.cos(a) + yy * math.sin(a)
    t = (t - t.min()) / max(t.max() - t.min(), 1e-9)
    return np.array(c0, dtype=float) * (1 - t[..., None]) + np.array(c1, dtype=float) * t[..., None]


def radial_field(cx, cy, rx, ry, power=2.0):
    xx, yy = coord_grid()
    d = ((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2
    return np.clip(1.0 - np.sqrt(d), 0.0, 1.0) ** power


def add_radial(px, cx, cy, rx, ry, color, strength, power=2.0):
    return px + radial_field(cx, cy, rx, ry, power)[..., None] * (np.array(color) * strength)


def _scratch():
    m = Image.new("L", (W * SS, H * SS), 0)
    return m, ImageDraw.Draw(m)


def _down(m):
    return np.asarray(m.resize((W, H), Image.BOX), dtype=np.float32) / 255.0


def poly_mask(points, ss=SS):
    m, d = _scratch()
    d.polygon([(x * W * ss, y * H * ss) for x, y in points], fill=255)
    return _down(m)


def poly_mask_all(polys, ss=SS):
    m, d = _scratch()
    for p in polys:
        d.polygon([(x * W * ss, y * H * ss) for x, y in p], fill=255)
    return _down(m)


def line_mask(segments, width_px, ss=SS, blur=0.0):
    if not segments:
        return np.zeros((H, W))
    m, d = _scratch()
    lw = max(1, int(width_px * ss))
    for (x0, y0), (x1, y1) in segments:
        d.line([(x0 * W * ss, y0 * H * ss), (x1 * W * ss, y1 * H * ss)], fill=255, width=lw)
    if blur:
        m = m.filter(ImageFilter.GaussianBlur(blur * ss))
    return _down(m)


def over(px, color, mask, alpha=1.0):
    a = (np.clip(mask, 0, 1) * alpha)[..., None]
    return px * (1 - a) + color * a


def screen(px, color, mask, strength=1.0):
    m = np.clip(mask, 0, 1) * strength
    lit = m[..., None] * np.asarray(color, dtype=float) if m.ndim == 2 else m
    return 1.0 - (1.0 - px) * (1.0 - lit)


def bloom(px, threshold=0.5, radius=36, strength=0.9):
    lum = px.max(axis=2)
    m = np.clip((lum - threshold) / max(1 - threshold, 1e-6), 0, 1)[..., None]
    bright = px * m
    img = Image.fromarray((np.clip(bright, 0, 1) * 255).astype(np.uint8))
    blurred = np.asarray(img.filter(ImageFilter.GaussianBlur(radius)), dtype=float) / 255.0
    return np.clip(px + blurred * strength, 0, 1)


def vignette(px, strength=0.5, power=1.7):
    xx, yy = coord_grid()
    d = np.sqrt((xx - 0.5) ** 2 + (yy - 0.5) ** 2) / 0.7071
    return px * (1.0 - (d**power) * strength)[..., None]


def grain(px, amount=0.014, seed=7):
    rng = np.random.default_rng(seed)
    n = rng.normal(0.0, 1.0, (H, W))
    return np.clip(px + (n * amount)[..., None], 0, 1)


def halftone(px, spacing, radius_of, color, strength, seed=3):
    rng = np.random.default_rng(seed)
    m = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(m)
    for j in range(int(H / spacing) + 2):
        for i in range(int(W / spacing) + 2):
            u = (i * spacing + (spacing / 2 if j % 2 else 0)) / W
            v = (j * spacing) / H
            if u > 1.05 or v > 1.05:
                continue
            t = radius_of(u, v) * (0.86 + 0.28 * rng.random())
            if t <= 0.02:
                continue
            r = t * spacing * 0.5
            d.ellipse([u * W - r, v * H - r, u * W + r, v * H + r], fill=int(255 * min(1.0, t)))
    m = m.filter(ImageFilter.GaussianBlur(0.6))
    return over(px, color, np.asarray(m, dtype=float) / 255.0, alpha=strength)


def finish(px, vig=0.46, seed=1, thr=0.50, bl=30, bs=0.60, g=0.012):
    px = bloom(px, threshold=thr, radius=bl, strength=bs)
    px = vignette(px, vig)
    return grain(px, g, seed=seed)


# ------------------------------------------------------------- 1. red slash


def red_slash():
    """The signature: three jagged red slashes cutting black, manga screentone."""
    px = canvas()
    px = add_radial(px, 0.20, 0.62, 0.80, 0.95, RED, 0.34, 2.2)
    px = add_radial(px, 0.86, 0.18, 0.55, 0.70, RED, 0.16, 2.4)
    px = add_radial(px, 0.55, 0.98, 0.70, 0.42, PINK, 0.09, 2.4)

    slashes = [
        [(0.05, 0.94), (0.19, 0.05), (0.30, 0.10), (0.17, 0.97)],
        [(0.43, 0.99), (0.56, 0.03), (0.65, 0.09), (0.55, 1.00)],
        [(0.77, 0.91), (0.88, 0.19), (0.98, 0.25), (0.90, 0.95)],
    ]
    g = linear_gradient((0.78, 0.02, 0.06), (1.00, 0.20, 0.28), 100)
    for pts in slashes:
        px = over(px, g, poly_mask(pts), alpha=0.98)
        inner = [(x + 0.030 * (0.5 - y) * 2, y) for x, y in pts]
        px = over(px, np.array((0.01, 0.01, 0.01)), poly_mask(inner), alpha=0.28)

    px = screen(px, WHITE, line_mask(
        [((0.00, 0.735), (1.00, 0.315)), ((0.00, 0.780), (1.00, 0.360))], 2.0, blur=0.3
    ), strength=0.90)
    px = screen(px, GOLD, line_mask([((0.30, 1.0), (0.72, 0.0))], 1.6, blur=0.3), strength=0.60)

    px = halftone(px, 15, lambda u, v: np.clip(1.25 - (0.55 * u + 0.95 * v), 0, 1) ** 1.5,
                  RED, 0.30, seed=11)
    def late(q):
        # drawn after bloom: bloom lifts near-saturated colours to white and
        # rotates their hue, which turned gold into yellow
        q = over(q, np.array(GOLD), poly_mask([(0.048, 0.215), (0.168, 0.088), (0.132, 0.300)]), alpha=0.97)
        q = over(q, np.array(WHITE), poly_mask([(0.862, 0.672), (0.945, 0.636), (0.952, 0.782)]), alpha=0.95)
        return q
    return px, late


# -------------------------------------------------------- 2. diagonal bars


def diagonal_bars():
    """Persona 5's loading screen: hard diagonal bars, one wide red band."""
    px = canvas()
    px = add_radial(px, 0.30, 0.30, 0.90, 0.95, RED, 0.11, 2.4)

    # 45-degree bars. Everything is keyed off the *phase* along the diagonal
    # rather than a distance from an absolute position, so coverage is a known
    # duty cycle and the pattern always crosses the frame.
    xx, yy = coord_grid()
    proj = (xx - 0.5) * 0.7071 + (yy - 0.5) * 0.7071   # distance along 45deg
    span = proj.max() - proj.min()
    unit = span / 15.0
    phase = proj / unit

    # the wide red band: an 18%-duty phase window, so it always lands on screen
    band = ((phase + 0.5) % 1.0) < 0.15
    px = over(px, linear_gradient((0.58, 0.02, 0.05), (0.98, 0.16, 0.23), 45), band.astype(float), alpha=0.98)

    # thin parallel bars, 7% duty, suppressed inside the wide band
    thin = ((phase % 1.0) < 0.05) & (~band)
    px = over(px, np.array(RED), thin.astype(float), alpha=0.80)

    # a black gap carves the wide band into two strokes
    gap = band & (((phase + 0.5) % 1.0) > 0.135)
    px = over(px, np.array(BLACK), gap.astype(float), alpha=0.95)

    # white hairline edge along the leading side of the band
    edge = (np.abs(((phase + 0.135) % 1.0)) < 0.012).astype(float)
    px = screen(px, WHITE, edge, strength=0.55)
    px = screen(px, WHITE, line_mask([((-0.1, 0.92), (1.1, -0.08))], 1.6, blur=0.3), strength=0.40)

    px = halftone(px, 16, lambda u, v: np.clip(0.55 + 0.75 * (0.5 * u + 0.6 * v), 0, 1) ** 1.6,
                  RED, 0.15, seed=5)
    def late(q):
        q = over(q, np.array(GOLD), poly_mask([(0.770, 0.052), (0.948, 0.148), (0.842, 0.352)]), alpha=0.97)
        return q
    return px, late


# --------------------------------------------------------------- 3. the mask


def mask_polygon(cx, cy, w, h, n=360, p=2.7, q=2.5, taper=0.52):
    """A domino-mask outline: rounded brow, tapering to a chin point."""
    pts = []
    for i in range(n):
        a = 2 * math.pi * i / n
        ca, sa = math.cos(a), math.sin(a)
        ex = math.copysign(abs(ca) ** (2 / p), ca)
        ey = math.copysign(abs(sa) ** (2 / q), sa)
        x = cx + (w / 2) * ex
        y = cy + (h / 2) * ey
        ty = max(0.0, (y - cy) / (h / 2))          # 0 at brow, 1 at chin
        x = cx + (x - cx) * (1.0 - taper * ty ** 1.7)
        pts.append((x, y))
    return pts


def domino_mask():
    """Joker's mask in white on black, split by a red slash."""
    px = canvas()
    px = add_radial(px, 0.46, 0.50, 0.66, 0.88, RED, 0.30, 2.2)
    px = add_radial(px, 0.14, 0.16, 0.46, 0.52, PINK, 0.07, 2.4)

    cx, cy, mw, mh = 0.46, 0.50, 0.50, 0.70
    shell = mask_polygon(cx, cy, mw, mh)

    # drop shadow so the mask sits above the black instead of dissolving into it
    shadow = [(x + 0.012, y + 0.016) for x, y in shell]
    px = over(px, np.array((0.16, 0.0, 0.03)), poly_mask(shadow), alpha=0.85)
    px = over(px, linear_gradient((0.66, 0.66, 0.66), (0.34, 0.34, 0.34), 105), poly_mask(shell), alpha=0.99)

    # angled eye cutouts, punched straight through to the black behind
    for sign in (-1, 1):
        ex = cx + sign * 0.108
        px = over(px, np.array(BLACK), poly_mask([
            (ex - 0.072, cy - 0.055), (ex + 0.055, cy - 0.082),
            (ex + 0.062, cy - 0.018), (ex - 0.065, cy + 0.012),
        ]), alpha=0.99)

    # the slash: a red band across the face, clipped to the mask (intersection,
    # not union -- a union here paints the whole face red and buries the eyes)
    slash = poly_mask([(-0.10, 0.700), (1.10, 0.420), (1.10, 0.590), (-0.10, 0.870)])
    px = over(px, linear_gradient((0.72, 0.02, 0.06), (1.00, 0.20, 0.28), 20),
              np.clip(slash, 0, 1) * poly_mask(shell), alpha=0.98)
    # white hairline on the slash's leading edge
    px = screen(px, WHITE, line_mask([((-0.10, 0.742), (1.10, 0.462))], 2.0, blur=0.3) * poly_mask(shell),
                strength=0.85)

    # the same slash continues past the mask, thinner, into the black field
    px = over(px, np.array(RED), np.clip(slash, 0, 1) * (1.0 - poly_mask(shell)) * 0.85, alpha=0.62)

    # gold chip on the brow
    def late(q):
        q = over(q, np.array(GOLD), poly_mask([
            (cx - 0.052, cy - 0.292), (cx + 0.052, cy - 0.322), (cx + 0.044, cy - 0.238)
        ]), alpha=0.97)
        return q

    px = halftone(px, 17, lambda u, v: np.clip(0.70 - np.sqrt((u - 0.46) ** 2 + (v - 0.86) ** 2) * 1.5, 0, 1) ** 1.3,
                  RED, 0.26, seed=8)
    return px, late


# ---------------------------------------------------------------- 4. impact


def impact_burst():
    """A comic impact frame: radial red speed lines exploding off-centre."""
    px = canvas()
    fx, fy = 0.36, 0.58
    px = add_radial(px, fx, fy, 0.72, 0.85, RED, 0.30, 2.0)
    px = add_radial(px, fx, fy, 0.16, 0.19, WHITE, 0.16, 2.6)

    xx, yy = coord_grid()
    ang = np.arctan2(yy - fy, (xx - fx) * (W / H))
    dist = np.sqrt(((xx - fx) * (W / H)) ** 2 + (yy - fy) ** 2)

    # tapered spokes, irregular like a hand-inked panel
    rng = np.random.default_rng(404)
    spokes = np.zeros((H, W))
    for k in range(58):
        a = 2 * math.pi * k / 58 + rng.normal(0, 0.045)
        half = 0.011 + 0.020 * rng.random()
        falloff = rng.uniform(0.45, 1.0)
        m = (np.abs(((ang - a + math.pi) % (2 * math.pi)) - math.pi) < half)
        reach = np.clip(1.0 - dist / (1.15 * falloff), 0, 1) ** 1.5
        spokes = np.maximum(spokes, (m * reach).astype(float))
    px = over(px, linear_gradient((0.70, 0.02, 0.06), (1.00, 0.18, 0.26), 30), spokes, alpha=0.97)

    # white core flash
    px = screen(px, WHITE, np.clip(1.0 - dist / 0.085, 0, 1) ** 2.2, strength=0.55)
    px = add_radial(px, fx, fy, 0.30, 0.34, PINK, 0.16, 2.2)

    # three hard slash wedges over the burst
    for pts, a in (
        ([[0.62, -0.05], [0.70, -0.05], [0.30, 1.05], [0.22, 1.05]], 0.97),
        ([[0.76, -0.05], [0.81, -0.05], [0.41, 1.05], [0.36, 1.05]], 0.80),
        ([[0.88, -0.05], [0.91, -0.05], [0.51, 1.05], [0.48, 1.05]], 0.65),
    ):
        px = over(px, np.array(RED), poly_mask(pts), alpha=a)
    px = screen(px, WHITE, line_mask([((0.60, 1.0), (0.90, 0.0))], 1.8, blur=0.3), strength=0.45)

    px = halftone(px, 14, lambda u, v: np.clip(0.95 - np.sqrt((u - fx) ** 2 + (v - fy) ** 2) * 1.1, 0, 1) ** 1.4,
                  RED, 0.26, seed=13)
    def late(q):
        q = over(q, np.array(GOLD), poly_mask([(0.042, 0.762), (0.196, 0.686), (0.152, 0.930)]), alpha=0.97)
        return q
    return px, late


# ------------------------------------------------------------------- driver

BUILDS = [
    ("1-red-slash.jpg", red_slash),
    ("2-diagonal-bars.jpg", diagonal_bars),
    ("3-domino-mask.jpg", domino_mask),
    ("4-impact-burst.jpg", impact_burst),
]

POST = {
    "1-red-slash.jpg": dict(seed=1),
    "2-diagonal-bars.jpg": dict(seed=2),
    "3-domino-mask.jpg": dict(vig=0.50, seed=3, thr=0.55, bl=26, bs=0.50),
    "4-impact-burst.jpg": dict(vig=0.48, seed=4, thr=0.50, bl=32, bs=0.70),
}


def save(px, name, quality=92):
    img = Image.fromarray((np.clip(px, 0, 1) * 255 + 0.5).astype(np.uint8))
    path = os.path.join(OUT, name)
    img.save(path, quality=quality, subsampling=1, optimize=True)
    return path


def main():
    only = sys.argv[1:] or None
    os.makedirs(OUT, exist_ok=True)
    for name, fn in BUILDS:
        if only and not any(o in name for o in only):
            continue
        t0 = time.time()
        raw, late = fn()
        px = finish(np.clip(raw, 0, 1), **POST.get(name, {}))
        px = np.clip(late(px), 0, 1)
        lum = px @ np.array([0.2126, 0.7152, 0.0722])
        path = save(px, name)
        print(
            f"{name:24s} {time.time() - t0:5.1f}s  mean={lum.mean():.3f} "
            f"p50={np.percentile(lum, 50):.3f} p95={np.percentile(lum, 95):.3f} "
            f"p99={np.percentile(lum, 99):.3f} max={lum.max():.2f} "
            f"{os.path.getsize(path) / 1024:.0f}KB"
        )


if __name__ == "__main__":
    main()
