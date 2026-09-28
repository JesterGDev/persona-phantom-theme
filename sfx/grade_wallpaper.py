#!/usr/bin/env python3
"""Grade arbitrary source art onto the Phantom Thieves palette.

Downloaded wallpapers arrive in whatever palette their artist chose -- the
Heijnsbroek canvases land around 0.33-0.73 mean luminance, against the theme's
0.16 ceiling, so a plain copy would look nothing like the rest of the set.

This maps each source through one shared grading curve: luminance is crushed
toward black, whatever red the source had is pushed to the theme's crimson, and
the top end is allowed to reach paper-white. Because every image goes through
the identical curve, images from different sources end up visually consistent,
which matters more here than preserving each artist's original colour.

Then crops to 16:9, choosing the band with the most detail rather than blindly
centring -- a centred crop of a tall canvas often lands on empty background.
"""

import argparse
import os

import numpy as np
from PIL import Image

Image.MAX_IMAGE_PIXELS = None

TARGET_W, TARGET_H = 2560, 1440
# all palette constants are 0..1 to match the working space; the previous
# 0..255 values silently saturated through the final clip
BLACK = np.array([8, 8, 10], np.float32) / 255.0
CRIMSON = np.array([230, 0, 18], np.float32) / 255.0
WHITE = np.array([242, 242, 242], np.float32) / 255.0
GOLD = np.array([255, 199, 44], np.float32) / 255.0

# Duotone stops. The structural ramp is keyed to *luminance*, not to source
# colour: gating warmth on how red the source already is leaves muted or
# warm-grey canvases with no crimson at all. Keying it to luminance guarantees
# every source lands on the palette, and source redness only tilts the result.
GAMMA = 2.1        # hard shadow crush; a plain gamma leaves too much mid-grey
SHADOW_MIN, SHADOW_MAX = 0.12, 0.62
BLACK_FRAC = 0.60       # share of pixels crushed to black; the GIF sits at 70-81%
ACC_FRAC = 0.05         # share of pixels that receive the gold accent
PLATEAU_LO = 0.45       # ramp position where crimson is reached
PLATEAU_HI = 0.62       # ramp position where crimson starts leaving for white
WHITE_CAP = 0.95        # highlight ceiling, keeps p99 under the 0.78 band
WARM_BIAS = 0.90        # how far a pixel is pulled toward the crimson ramp
ACCENT = 0.90           # strength of the gold highlight


def adaptive_shadow(lum, black_frac=BLACK_FRAC):
    """Pick the shadow point per image so a fixed share of pixels go black.

    A single global constant cannot serve both a pale watercolour and a dark
    gouache: the watercolour stays washed out no matter how far the constant is
    raised. Deriving the stop from each image's own luminance keeps the
    black-dominant balance the theme depends on regardless of source exposure.
    """
    p = float(np.percentile(lum, black_frac * 100.0))
    return float(np.clip(p * 0.92, SHADOW_MIN, SHADOW_MAX))


def grade(a):
    """a: HxWx3 float in 0..1. Returns the graded image in 0..1."""
    lum = a[..., 0] * 0.2126 + a[..., 1] * 0.7152 + a[..., 2] * 0.0722

    # How red this pixel already is. Must compare the red channel against the
    # strongest *competing* channel: comparing it against the per-pixel max is
    # always <= 0, since red can never exceed the max and still be positive.
    other = a[..., 1:].max(axis=2)
    redness = np.clip((a[..., 0] - other) / 0.20, 0, 1)

    # crush the low end
    shadow = adaptive_shadow(lum)
    l = np.clip((lum - shadow) / (1.0 - shadow), 0, 1) ** GAMMA

    # structural ramp: climb to crimson, HOLD it across a wide plateau, then
    # leave for paper white. The plateau is what puts large flat crimson fields
    # in the output; a continuous ramp almost never lands on pure crimson, which
    # is why an earlier version measured 0% red coverage.
    cap = WHITE * WHITE_CAP
    t1 = np.clip(l / PLATEAU_LO, 0, 1)
    warm = BLACK + (CRIMSON - BLACK) * t1[..., None]
    t2 = np.clip((l - PLATEAU_HI) / (1.0 - PLATEAU_HI), 0, 1)
    warm = warm + (cap - warm) * t2[..., None]

    # the neutral path keeps more of its value so non-red structure survives
    cool = BLACK + (cap - BLACK) * (l ** 1.30)[..., None] * 0.62

    # pull hard toward the warm ramp: a high bias is what makes images from
    # different sources read as one set
    bias = np.clip(redness * 0.20 + WARM_BIAS, 0, 1)
    out = cool + (warm - cool) * bias[..., None]

    # A whisper of gold in the brightest highlights: the theme's muted accent,
    # and the only thing keeping the set from reading as pure duotone.
    # Keyed to a luminance *percentile* rather than a fixed threshold -- with
    # an adaptive shadow almost nothing reaches a high fixed value, which left
    # the accent at literally 0% coverage on every image.
    cut = float(np.percentile(l, 100.0 - ACC_FRAC * 100.0))
    # the 0.45 exponent sharpens the band so the selected pixels actually
    # reach gold; a linear ramp left almost the whole band at partial blend
    hot = np.clip((l - cut) / max(1e-6, 1.0 - cut), 0, 1) ** 0.45
    out = out + (GOLD - out) * (hot * ACCENT)[..., None]
    return np.clip(out, 0, 1)


def best_band(a, aspect):
    """Pick the horizontal band with the most detail, for a 16:9 crop."""
    h, w = a.shape[:2]
    band = int(w / aspect)
    if band >= h:
        return 0, h
    # detail = local contrast, measured in grayscale on a cheap downsample
    small = a[::max(1, h // 400), ::max(1, w // 400)]
    gl = small.mean(axis=2)
    scores = []
    step = max(1, band // 40)
    for y in range(0, h - band + 1, step):
        seg = gl[y // max(1, h // 400):(y + band) // max(1, h // 400)]
        if seg.size == 0:
            scores.append(0.0)
            continue
        scores.append(float(seg.std()))
    best = int(np.argmax(scores)) * step
    return min(best, h - band), band


def process(src, dst, size=(TARGET_W, TARGET_H)):
    im = Image.open(src).convert("RGB")
    a = np.asarray(im, np.float32) / 255.0

    g = grade(a)

    aspect = size[0] / size[1]
    y0, band = best_band(a, aspect)
    h, w = g.shape[:2]
    x0 = max(0, (w - int(band * aspect)) // 2)
    crop = g[y0:y0 + band, x0:x0 + int(band * aspect)]

    out = Image.fromarray((np.clip(crop, 0, 1) * 255).astype(np.uint8), "RGB")
    out = out.resize(size, Image.LANCZOS)
    out.save(dst, "JPEG", quality=92, optimize=True, progressive=True)
    return out


def stats(path):
    a = np.asarray(Image.open(path).convert("RGB").resize((640, 360)),
                   np.float32) / 255.0
    lum = a[..., 0] * 0.2126 + a[..., 1] * 0.7152 + a[..., 2] * 0.0722
    red = (np.abs(a - CRIMSON).sum(2) < 0.35).mean() * 100
    acc = (np.abs(a - GOLD).sum(2) < 0.45).mean() * 100
    return dict(mean=lum.mean(), med=np.median(lum), p99=np.percentile(lum, 99),
                std=lum.std(), red=red, acc=acc)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("dst")
    a = ap.parse_args()
    process(a.src, a.dst)
    s = stats(a.dst)
    print(f"{os.path.basename(a.dst)}  mean {s['mean']:.3f}  med {s['med']:.3f}  "
          f"p99 {s['p99']:.3f}  std {s['std']:.3f}  red {s['red']:.1f}%  acc {s['acc']:.2f}%")
