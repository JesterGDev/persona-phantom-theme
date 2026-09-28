#!/usr/bin/env python3
"""Phantom Thieves motion-graphics loop.

An original, seamlessly looping background built from Persona-style
geometry: diagonal slashes, a halftone field, expanding rings, a rotating
triangle, and a skewed title with a periodic RGB-split glitch.

Seamlessness is structural rather than cross-faded. Every animation is a
function of a phase p in [0,1) and only uses operations that are periodic in
p (sine, or modulo), so frame 0 and frame N are the same image. Nothing is
faded at the seam, because there is no seam.
"""

import math
import os
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H = 1280, 720
GIF_W, GIF_H = 512, 288       # GIF is the wallpaper, so it carries the size
GIF_FPS = 12                  # the motion is slow; 12fps is indistinguishable
GIF_COLORS = 64               # and each dropped frame is ~70KB
FPS = 20
SECONDS = 4
FRAMES = FPS * SECONDS

BLACK = (8, 8, 10)
CRIMSON = (230, 0, 18)
WHITE = (242, 242, 242)
GOLD = (255, 199, 44)

OUT_GIF = os.path.expanduser(
    "~/.config/omarchy/themes/phantom-thieves/backgrounds/5-motion-loop.gif")
OUT_MP4 = os.path.expanduser("~/.local/share/omarchy/phantom-thieves/motion-loop.mp4")
FRAME_DIR = "/tmp/opencode/motion_frames"
FONT = os.path.expanduser(
    "~/.local/share/fonts/phantom-thieves/BarlowCondensed-ExtraBold.ttf")


def ease(t):
    return t * t * (3 - 2 * t)


def base_field(p):
    """Background: near-black with a crimson bloom that breathes."""
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    x = xx / W
    y = yy / H
    # radial falloff centred off to the right, pulsing over the loop
    cx, cy = 0.72, 0.42
    r = np.sqrt((x - cx) ** 2 + ((y - cy) * 0.62) ** 2)
    pulse = 0.5 + 0.5 * math.sin(2 * math.pi * p)
    # Keep the bloom a tint over black, not a wash. At full strength this
    # pushed R above 90 across ~90% of the frame, which turns the loop into a
    # full-screen red flash every few seconds.
    bloom = np.clip(1.0 - r / (0.34 + 0.07 * pulse), 0, 1) ** 2
    img = np.zeros((H, W, 3), np.float32)
    img += np.array(BLACK, np.float32)
    img += bloom[..., None] * np.array(CRIMSON, np.float32) * (0.16 + 0.05 * pulse)
    return img, xx, yy


def slashes(img, xx, yy, p):
    """Hard-edged diagonal bars. Modulo keeps each bar on a closed path."""
    diag = (xx * 0.7071 + yy * 0.7071)
    span = (W + H) * 0.7071
    bars = [
        # (speed, half-width fraction, alpha, colour, drift)
        (1.0, 0.085, 1.00, CRIMSON, 0.0),
        (-1.0, 0.022, 1.00, WHITE, 0.37),
        (2.0, 0.030, 0.60, CRIMSON, 0.11),
    ]
    for speed, width, alpha, colour, drift in bars:
        # position wraps over one span -> identical at p=0 and p=1
        pos = (p * speed + drift) % 1.0
        centre = pos * span
        dist = np.abs(((diag - centre + span / 2) % span) - span / 2)
        m = np.clip(1.0 - dist / (span * width), 0, 1) ** 0.6
        img += m[..., None] * np.array(colour, np.float32) * alpha * 0.95
    return img


def halftone(img, xx, yy, p):
    """Dot field whose dot size rides a travelling sine wave."""
    spacing = 22.0
    gx = (xx % spacing) - spacing / 2
    gy = (yy % spacing) - spacing / 2
    d = np.sqrt(gx * gx + gy * gy)
    wave = 0.5 + 0.5 * np.sin(2 * math.pi * (p + xx / (W * 1.6) + yy / (H * 2.4)))
    radius = 1.0 + 7.4 * wave ** 2
    # fade the field out toward the top so it never fights the title
    fade = np.clip((yy / H - 0.18) / 0.55, 0, 1)
    m = np.clip(radius - d, 0, 1) * fade
    # dots are white where the wave crests, crimson in the troughs
    tint = np.where(wave[..., None] > 0.55, np.array(WHITE, np.float32),
                    np.array(CRIMSON, np.float32))
    img += m[..., None] * tint * 0.55
    return img


def rings(img, xx, yy, p):
    """Three expanding rings, phase-offset by a third so the set repeats."""
    x = (xx / W - 0.5)
    y = (yy / H - 0.5) * (H / W) * 2.0
    r = np.sqrt(x * x + y * y)
    maxr = 0.95
    for k in range(3):
        ph = (p + k / 3.0) % 1.0
        radius = ease(ph) * maxr
        band = np.exp(-((r - radius) ** 2) / (2 * 0.016 ** 2))
        fade = math.sin(math.pi * ph) ** 0.6      # birth and death, not a cut
        tint = CRIMSON if k % 2 == 0 else WHITE
        img += band[..., None] * np.array(tint, np.float32) * fade * 0.5
    return img


def triangle_layer(p, scale=1.0, width=5):
    """Outlined triangle rotating exactly once per loop -> seamless."""
    S = 3
    layer = Image.new("L", (W * S, H * S), 0)
    d = ImageDraw.Draw(layer)
    cx, cy = W * 0.30 * S, H * 0.52 * S
    r = min(W, H) * 0.30 * scale * S
    ang = 2 * math.pi * p
    pts = []
    for i in range(3):
        a = ang - math.pi / 2 + i * 2 * math.pi / 3
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    d.polygon(pts, outline=255, width=int(width * S))
    layer = layer.resize((W, H), Image.LANCZOS)
    return layer


def title_layer(p):
    """Small skewed corner tag, periodically glitched and wiped in.

    Deliberately not a full-width title. At display size the words spanned
    most of the frame in crimson, which pushed the median pixel to pure
    crimson and read as a red screen flash; on a desktop it would also fight
    every window opened over it.
    """
    S = 2
    layer = Image.new("RGBA", (W * S, H * S), (0, 0, 0, 0))
    font = ImageFont.truetype(FONT, int(62 * S))
    text = "PHANTOM THIEVES"

    # wipe: a hard edge travelling across, periodic in p
    edge = ((p * 2.0) % 1.0)
    wipe = Image.new("L", layer.size, 0)
    ImageDraw.Draw(wipe).rectangle(
        [0, 0, layer.size[0] * (0.18 + 0.9 * edge), layer.size[1]], fill=255)

    base = Image.new("RGBA", layer.size, (0, 0, 0, 0))
    bd = ImageDraw.Draw(base)
    bd.text((int(64 * S), int(H * 0.79 * S)), text, font=font,
            fill=(*CRIMSON, 255))

    # RGB split: two crimson echoes of the text, offset in opposite
    # directions. The offset images must be masked by the *text alpha* --
    # pasting a solid fill with itself as the mask floods the whole layer.
    split = int(9 * S * (0.5 + 0.5 * math.sin(2 * math.pi * p * 2)))
    text_alpha = base.getchannel("A")
    red_echo = Image.new("RGBA", layer.size, (*CRIMSON, 255))
    red_echo.putalpha(text_alpha)
    base_rgb = Image.new("RGBA", layer.size, (0, 0, 0, 0))
    base_rgb.paste(red_echo, (split, 0), red_echo)
    base_rgb.paste(red_echo, (-split, 0), red_echo)
    base_rgb.paste(base, (0, 0), base)

    # slice displacement: per-row sine offset, periodic in p
    shifted = Image.new("RGBA", layer.size, (0, 0, 0, 0))
    sd = ImageDraw.Draw(shifted)
    band = 7 * S
    for y0 in range(0, layer.size[1], band):
        amp = int(26 * S * math.sin(2 * math.pi * (p * 3 + y0 / 90.0)))
        if amp:
            shifted.paste(base_rgb.crop((0, y0, layer.size[0], y0 + band)),
                         (amp, y0))
        else:
            shifted.paste(base_rgb.crop((0, y0, layer.size[0], y0 + band)),
                         (0, y0))
    del sd

    # skew hard to the right, the way the game's type leans
    shear = 0.22
    skewed = shifted.transform(
        layer.size, Image.AFFINE, (1, shear, -shear * layer.size[1] * 0.62, 0, 1, 0),
        resample=Image.BICUBIC)
    alpha = skewed.getchannel("A").point(lambda v: v)
    alpha = Image.composite(alpha, Image.new("L", layer.size, 0), wipe)
    skewed.putalpha(alpha)
    return skewed.resize((W, H), Image.LANCZOS)


def render(p):
    # Wrap first. p=1.0 must reduce to exactly 0.0, not merely to a
    # numerically-equal float: without this, accumulated float error puts the
    # triangle's vertices a fraction of a pixel off at the seam, and those
    # high-contrast edge pixels are the one thing that reads as a jump.
    p = p % 1.0
    img, xx, yy = base_field(p)
    img = slashes(img, xx, yy, p)
    img = halftone(img, xx, yy, p)
    img = rings(img, xx, yy, p)
    img = np.clip(img, 0, 255)

    frame = Image.fromarray(img.astype(np.uint8), "RGB").convert("RGBA")

    tri = triangle_layer(p)
    if p < 0.5:                      # triangle pulses out and back
        tri = tri.point(lambda v: v)
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    overlay.paste(Image.new("RGBA", (W, H), (*WHITE, 255)), (0, 0), tri)
    # a crimson ghost of the triangle, offset, for depth
    ghost = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ghost.paste(Image.new("RGBA", (W, H), (*CRIMSON, 255)), (10, 8), tri)
    frame = Image.alpha_composite(frame, ghost)
    frame = Image.alpha_composite(frame, overlay)

    frame = Image.alpha_composite(frame, title_layer(p))

    # Fine grain, but STATIC: a fresh random field every frame looks the same
    # to the eye and compresses far better. Animated noise costs ~10x in the
    # GIF because every frame differs in every pixel, which is what wrecks
    # LZW delta coding. Kept low too -- at GIF's 128-colour palette, grain
    # over the large black areas turns into dither noise and doubles the file.
    rng = np.random.default_rng(7)
    noise = rng.normal(0, 1.5, (H, W, 1)).astype(np.float32)
    arr = np.clip(np.asarray(frame.convert("RGB"), np.float32) + noise, 0, 255)
    return Image.fromarray(arr.astype(np.uint8), "RGB")


def main():
    os.makedirs(FRAME_DIR, exist_ok=True)
    for f in os.listdir(FRAME_DIR):
        os.remove(os.path.join(FRAME_DIR, f))
    os.makedirs(os.path.dirname(OUT_GIF), exist_ok=True)
    os.makedirs(os.path.dirname(OUT_MP4), exist_ok=True)

    print(f"rendering {FRAMES} frames at {W}x{H}...")
    for i in range(FRAMES):
        p = i / FRAMES
        render(p).save(os.path.join(FRAME_DIR, f"f{i:04d}.png"))
        if i % 12 == 0:
            print(f"  frame {i}/{FRAMES}")

    print("encoding mp4...")
    subprocess.run([
        "ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS),
        "-i", f"{FRAME_DIR}/f%04d.png",
        "-c:v", "libx264", "-preset", "slow", "-crf", "20",
        "-pix_fmt", "yuv420p", "-movflags", "+faststart", OUT_MP4], check=True)

    print("encoding gif (optimised palette)...")
    # two-pass palette: a shared 128-colour palette across the whole loop
    # beats per-frame palettes, both in size and in stability (no colour
    # shimmer between frames)
    pal = OUT_GIF + ".pal.png"
    subprocess.run([
        "ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS),
        "-i", f"{FRAME_DIR}/f%04d.png", "-vf",
        f"fps={GIF_FPS},scale={GIF_W}:{GIF_H}:flags=lanczos,"
        f"palettegen=max_colors={GIF_COLORS}:stats_mode=diff",
        pal], check=True)
    subprocess.run([
        "ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS),
        "-i", f"{FRAME_DIR}/f%04d.png", "-i", pal, "-filter_complex",
        f"[0:v]fps={GIF_FPS},scale={GIF_W}:{GIF_H}:flags=lanczos[x];"
        f"[x][1:v]paletteuse=dither=bayer:bayer_scale=4:diff_mode=rectangle",
        "-loop", "0", OUT_GIF], check=True)
    os.remove(pal)

    for path in (OUT_GIF, OUT_MP4):
        print(f"  {path}  {os.path.getsize(path)/1024/1024:.2f} MB")
    print(f"  {W}x{H} @ {FPS}fps, {SECONDS}s, {FRAMES} frames")


if __name__ == "__main__":
    sys.exit(main())
