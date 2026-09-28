#!/usr/bin/env python3
"""Classify wallpaper pixels by HSV bucket -- verifies a Persona palette is
actually present instead of guessing from luminance alone."""
import glob
import os
import sys
import numpy as np
from PIL import Image


def rgb2hsv(px):
    r, g, b = px[..., 0], px[..., 1], px[..., 2]
    mx, mn = px.max(-1), px.min(-1)
    d = mx - mn
    h = np.zeros_like(mx)
    nz = d > 1e-8
    rm = nz & (mx == r); gm = nz & (mx == g); bm = nz & (mx == b)
    h[rm] = (60 * ((g[rm] - b[rm]) / d[rm])) % 360
    h[gm] = (60 * ((b[gm] - r[gm]) / d[gm]) + 120)
    h[bm] = (60 * ((r[bm] - g[bm]) / d[bm]) + 240)
    s = np.where(mx > 1e-8, d / np.maximum(mx, 1e-8), 0)
    return h, s, mx


def classify(px, tol=7.0):
    h, s, v = rgb2hsv(px)
    hd = (h + 180) % 360 - 180          # signed hue offset from red (0 deg)
    return {
        "red":   (np.abs(hd) < tol) & (s > 0.45) & (v > 0.30),
        "pink":  (np.abs(hd + 24) < 12) & (s > 0.20) & (v > 0.40),   # Panther #ff5c8a
        "gold":  (np.abs(hd - 45) < 9) & (s > 0.45) & (v > 0.55),    # Fox    #ffc72c
        "white": (s < 0.12) & (v > 0.55),                            # light neutral
        "black": v < 0.14,
    }


names = sys.argv[1:] or sorted(
    glob.glob(os.path.expanduser(
        "~/.config/omarchy/themes/phantom-thieves/backgrounds/*.jpg")))

fail = False
for path in names:
    px = np.asarray(Image.open(path).convert("RGB"), dtype=float) / 255.0
    c = classify(px)
    tot = {k: v.mean() for k, v in c.items()}
    lum = px @ np.array([0.2126, 0.7152, 0.0722])
    mean_l, med_l, p99_l = lum.mean(), np.percentile(lum, 50), np.percentile(lum, 99)
    accent = max(tot["white"], tot["gold"], tot["pink"])
    # What actually matters for a desktop background:
    #  - the typical field is dark, so text/icons read on top
    #  - no blown highlights
    #  - Persona identity: real red present
    #  - at least one bright accent so it isn't flat
    # A bold graphic element (a mask) is allowed; a bright field is not.
    checks = [
        (mean_l < 0.16,  f"mean={mean_l:.3f}<0.16"),
        (med_l < 0.12,   f"median={med_l:.3f}<0.12"),
        (p99_l < 0.78,   f"p99={p99_l:.3f}<0.78"),
        (tot["red"] > 0.06, f"red={tot['red']*100:.1f}%>6%"),
        (accent > 0.0015,   f"accent={accent*100:.2f}%>0.15%"),
    ]
    ok = all(c0 for c0, _ in checks)
    fail = fail or not ok
    detail = "  ".join(msg for c0, msg in checks if not c0) or "all ok"
    print(f"{'PASS' if ok else 'FAIL'} {os.path.basename(path)[:-4]:18s} " +
          "  ".join(f"{k}={v*100:5.2f}" for k, v in tot.items()) + f"  | {detail}")
sys.exit(1 if fail else 0)
