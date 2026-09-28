#!/usr/bin/env python3
"""Tune the grade against the theme's existing wallpapers as the reference.

Rather than pick targets by intuition, this measures the four procedural
wallpapers already in the theme and fits the grade so downloaded sources land
in the same bands. Scoring rewards landing inside the observed range and
penalises being far from it, so a result that merely squeaks past a threshold
does not beat one that matches the set.
"""

import itertools
import os

import numpy as np
from PIL import Image

Image.MAX_IMAGE_PIXELS = None
import importlib.util

spec = importlib.util.spec_from_file_location("gw", "/tmp/opencode/grade_wallpaper.py")
gw = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gw)

BG = "/home/dawar/.config/omarchy/themes/phantom-thieves/backgrounds"


def measure(a):
    lum = a[..., 0] * 0.2126 + a[..., 1] * 0.7152 + a[..., 2] * 0.0722
    red = (np.abs(a - gw.CRIMSON).sum(2) < 0.30).mean() * 100
    acc = (np.abs(a - gw.GOLD).sum(2) < 0.40).mean() * 100
    return dict(mean=float(lum.mean()), med=float(np.median(lum)),
                p99=float(np.percentile(lum, 99)), std=float(lum.std()),
                red=float(red), acc=float(acc))


ref = []
for f in sorted(os.listdir(BG)):
    if f.endswith(".jpg"):
        a = np.asarray(Image.open(os.path.join(BG, f)).convert("RGB")
                       .resize((640, 360)), np.float32) / 255.0
        ref.append(measure(a))

RANGES = {k: (min(r[k] for r in ref), max(r[k] for r in ref)) for k in ref[0]}
print("reference ranges from existing set:")
for k, (lo, hi) in RANGES.items():
    print(f"  {k:5s} {lo:.3f} .. {hi:.3f}")

# Point targets, not just a range. Scoring purely on "inside the observed range"
# drives red to 0%, which sits just above the set's low bound and therefore wins
# -- yet a Persona 5 wallpaper with no crimson is plainly wrong. Red is aimed
# high in the observed range on purpose; the rest sit at the range midpoint.
GOAL = dict(mean=0.125, med=0.058, p99=0.640, std=0.145, red=8.0, acc=1.0)
TOL = dict(mean=0.030, med=0.020, p99=0.130, std=0.040, red=6.0, acc=0.9)


def fit_score(s):
    """Normalised squared distance to the point targets."""
    tot = 0.0
    for k, g in GOAL.items():
        tot += ((s[k] - g) / TOL[k]) ** 2
    return tot


srcs = []
for f in sorted(os.listdir("/tmp/opencode/raw")):
    if not f.lower().endswith((".jpg", ".png")):
        continue
    a = np.asarray(Image.open(os.path.join("/tmp/opencode/raw", f)).convert("RGB"),
                   np.float32) / 255.0
    h, w = a.shape[:2]
    sc = max(1, h // 800)
    srcs.append((f, np.ascontiguousarray(a[::sc, ::sc])))


def run(a, bias, acc, accfrac, blackfrac, plo, phi):
    gw.WARM_BIAS = bias
    gw.ACCENT = acc
    gw.ACC_FRAC = accfrac
    gw.BLACK_FRAC = blackfrac
    gw.PLATEAU_LO = plo
    gw.PLATEAU_HI = phi
    lum = a[..., 0] * 0.2126 + a[..., 1] * 0.7152 + a[..., 2] * 0.0722
    other = a[..., 1:].max(axis=2)
    redness = np.clip((a[..., 0] - other) / 0.20, 0, 1)
    shadow = gw.adaptive_shadow(lum, blackfrac)
    l = np.clip((lum - shadow) / (1.0 - shadow), 0, 1) ** gw.GAMMA
    cap = gw.WHITE * gw.WHITE_CAP
    t1 = np.clip(l / gw.PLATEAU_LO, 0, 1)
    warm = gw.BLACK + (gw.CRIMSON - gw.BLACK) * t1[..., None]
    t2 = np.clip((l - gw.PLATEAU_HI) / (1.0 - gw.PLATEAU_HI), 0, 1)
    warm = warm + (cap - warm) * t2[..., None]
    cool = gw.BLACK + (cap - gw.BLACK) * (l ** 1.30)[..., None] * 0.62
    b = np.clip(redness * 0.20 + bias, 0, 1)
    out = cool + (warm - cool) * b[..., None]
    cut = float(np.percentile(l, 100.0 - accfrac * 100.0))
    hot = np.clip((l - cut) / max(1e-6, 1.0 - cut), 0, 1) ** 0.45
    out = out + (gw.GOLD - out) * (hot * acc)[..., None]
    return np.clip(out, 0, 1)


best = None
for bias, acc, accfrac, blackfrac, plo, phi in itertools.product(
        (0.90, 0.95, 1.00), (0.70, 0.90, 1.00),
        (0.015, 0.030, 0.050), (0.50, 0.60, 0.70),
        (0.30, 0.38, 0.45), (0.42, 0.48, 0.55, 0.62)):
    tot = 0.0
    for _f, a in srcs:
        h, w = a.shape[:2]
        band = int(w / (16 / 9))
        if band < h:
            y = (h - band) // 2
            a2 = a[y:y + band, :int(band * 16 / 9)]
        else:
            a2 = a
        tot += fit_score(measure(run(a2, bias, acc, accfrac, blackfrac, plo, phi)))
    if best is None or tot < best[0]:
        best = (tot, (bias, acc, accfrac, blackfrac, plo, phi))

print(f"\nbest = {best[0]:.3f}  (BIAS, ACCENT, ACC_FRAC, BLACK_FRAC, PLO, PHI) = {best[1]}")
bias, acc, accfrac, blackfrac, plo, phi = best[1]
print(f"\n{'file':12s} {'mean':>6s} {'med':>6s} {'p99':>6s} {'std':>6s} {'red%':>6s} {'acc%':>6s}  dist")
for f, a in srcs:
    h, w = a.shape[:2]
    band = int(w / (16 / 9))
    if band < h:
        y = (h - band) // 2
        a2 = a[y:y + band, :int(band * 16 / 9)]
    else:
        a2 = a
    s = measure(run(a2, bias, acc, accfrac, blackfrac, plo, phi))
    print(f"{f:12s} {s['mean']:6.3f} {s['med']:6.3f} {s['p99']:6.3f} {s['std']:6.3f} "
          f"{s['red']:6.1f} {s['acc']:6.2f}  {fit_score(s):.2f}")
