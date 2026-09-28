#!/usr/bin/env python3
"""Compose a Phantom Thieves theme preview: wallpaper + representative chrome.

Everything is read from the theme's own colors.toml, so re-running after a
palette change keeps the preview honest. Output is 1800x1012 PNG8, matching the
convention of the themes shipped with Omarchy.
"""

import os
import re
import tomllib

from PIL import Image, ImageDraw, ImageFilter

THEME = os.path.expanduser("~/.config/omarchy/themes/phantom-thieves")
OUT = os.path.join(THEME, "preview.png")
W, H = 1800, 1012
SS = 2  # supersample, then downscale for clean edges


def load_colors():
    with open(os.path.join(THEME, "colors.toml"), "rb") as f:
        return {k: v.lstrip("#") for k, v in tomllib.load(f).items()
                if isinstance(v, str) and re.fullmatch(r"[0-9a-fA-F]{6}", v.lstrip("#"))}


def rgb(h):
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


C = load_colors()
BG = rgb(C["background"])
DARK = rgb(C["dark_background"])
LIGHTER = rgb(C["lighter_background"])
ACCENT = rgb(C["accent"])
PINK = rgb(C["magenta"])
GOLD = rgb(C["yellow"])
FG = rgb(C["foreground"])
MUTED = rgb(C["muted"])
SELECT = rgb(C["selection"])


def chamfer(draw, box, cut, fill, outline=None, width=3):
    """The angular panel shape used across the shell chrome."""
    x0, y0, x1, y1 = box
    pts = [(x0 + cut, y0), (x1, y0), (x1, y1 - cut), (x1 - cut, y1), (x0, y1), (x0, y0 + cut)]
    draw.polygon(pts, fill=fill, outline=outline, width=width)


def bar(draw, box, color, radius=3):
    draw.rounded_rectangle(box, radius=radius, fill=color)


def build():
    bg = Image.open(os.path.join(THEME, "backgrounds", "1-red-slash.jpg")).convert("RGB")
    # centre-crop the wallpaper to 16:9
    scale = max(W / bg.width, H / bg.height)
    bg = bg.resize((int(bg.width * scale + 1), int(bg.height * scale + 1)), Image.LANCZOS)
    left = (bg.width - W) // 2
    top = int((bg.height - H) * 0.42)          # bias up: keep the slash field
    canvas = bg.crop((left, top, left + W, top + H)).convert("RGBA")

    lay = Image.new("RGBA", (W * SS, H * SS), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    s = SS

    def S(v):
        return v * s

    # --- top bar ---
    d.rectangle([0, 0, S(W), S(38)], fill=DARK + (238,))
    d.line([0, S(38), S(W), S(38)], fill=ACCENT + (150,), width=S(2))
    for i in range(5):                            # workspace pips
        x = 26 + i * 40
        col = ACCENT if i == 1 else MUTED
        d.rectangle([S(x), S(14), S(x + 22), S(24)], fill=col + (255,))
    d.rounded_rectangle([S(W - 300), S(11), S(W - 26), S(27)], radius=S(8), fill=SELECT + (255,))
    bar(d, [S(W - 286), S(16), S(W - 150), S(22)], FG + (150,), S(3))
    bar(d, [S(W - 138), S(16), S(W - 96), S(22)], PINK + (200,), S(3))
    bar(d, [S(W - 84), S(16), S(W - 40), S(22)], GOLD + (200,), S(3))

    # --- main terminal window ---
    win = (58, 74, 1180, 880)
    chamfer(d, [S(win[0]), S(win[1]), S(win[2]), S(win[3])], S(20), DARK + (252,), ACCENT + (255,), S(4))
    d.rectangle([S(win[0] + 20), S(win[1] + 20), S(win[2] - 20), S(win[1] + 62)], fill=LIGHTER + (255,))
    for i, c in enumerate([ACCENT, PINK, GOLD, MUTED]):
        d.ellipse([S(win[0] + 34 + i * 26), S(win[1] + 33), S(win[0] + 48 + i * 26), S(win[1] + 47)], fill=c + (255,))
    # prompt lines: coloured prefix then dim text, in the theme's ANSI ramp
    ramp = [FG, ACCENT, PINK, GOLD, rgb(C["cyan"]), rgb(C["blue"]), rgb(C["green"])]
    rng = __import__("random").Random(5)
    y = win[1] + 96
    for i in range(22):
        if y > win[3] - 40:
            break
        c = ramp[i % len(ramp)]
        if i % 5 == 0:                              # a prompt
            bar(d, [S(win[0] + 34), S(y), S(win[0] + 62), S(y + 13)], c + (255,), S(2))
            x = win[0] + 72
        else:
            x = win[0] + 34
        wpx = rng.randint(120, 720)
        bar(d, [S(x), S(y), S(x + wpx), S(y + 13)], c + (190,), S(2))
        y += 30

    # --- launcher panel, chamfered, magenta accent ---
    lp = (1216, 132, 1744, 470)
    chamfer(d, [S(lp[0]), S(lp[1]), S(lp[2]), S(lp[3])], S(16), DARK + (252,), PINK + (255,), S(3))
    d.rectangle([S(lp[0] + 16), S(lp[1] + 16), S(lp[2] - 16), S(lp[1] + 74)], fill=SELECT + (255,))
    bar(d, [S(lp[0] + 34), S(lp[1] + 36), S(lp[2] - 60), S(lp[1] + 56)], FG + (170,), S(3))
    for i in range(5):
        yy = lp[1] + 100 + i * 60
        if i == 1:
            chamfer(d, [S(lp[0] + 16), S(yy), S(lp[2] - 16), S(yy + 48)], S(8), SELECT + (255,))
        col = ACCENT if i % 2 == 0 else FG
        bar(d, [S(lp[0] + 34), S(yy + 12), S(lp[0] + 50), S(yy + 34)], col + (235,), S(3))
        bar(d, [S(lp[0] + 64), S(yy + 18), S(lp[0] + 64 + 200 - i * 22), S(yy + 30)],
            col + (185 if i == 1 else 130,), S(3))

    # --- notification, gold accent ---
    nt = (1216, 520, 1744, 646)
    chamfer(d, [S(nt[0]), S(nt[1]), S(nt[2]), S(nt[3])], S(12), DARK + (250,), GOLD + (235,), S(3))
    d.rectangle([S(nt[0] + 6), S(nt[1] + 10), S(nt[0] + 16), S(nt[3] - 10)], fill=GOLD + (255,))
    bar(d, [S(nt[0] + 32), S(nt[1] + 26), S(nt[2] - 90), S(nt[1] + 40)], FG + (200,), S(3))
    bar(d, [S(nt[0] + 32), S(nt[1] + 52), S(nt[2] - 190), S(nt[1] + 66)], FG + (120,), S(3))

    lay = lay.resize((W, H), Image.LANCZOS)
    out = Image.alpha_composite(canvas, lay).convert("RGB")
    out.save(OUT, optimize=True)
    return out


if __name__ == "__main__":
    im = build()
    print(f"wrote {OUT} {im.size} {im.mode} {os.path.getsize(OUT) / 1024:.0f}KB")
