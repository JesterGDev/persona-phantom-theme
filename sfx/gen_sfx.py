#!/usr/bin/env python3
"""Phantom Thieves UI sound set -- synthesised from scratch.

Nothing here is sampled, traced or reproduced: every waveform is generated
mathematically (oscillators, noise, filters, envelopes) and every note is an
original short motif written for this set. The brief is Persona 5's sonic
character -- hard transients, detuned string stabs, a jazzy minor-key colour
-- without borrowing any of its actual music or effects.
"""

import math
import os
import struct
import wave

import numpy as np

SR = 48000
# Renders straight into the live install. Override with PHANTOM_SFX_OUT to
# render somewhere else (packaging, a checked-in wav/ directory, CI).
OUT = os.path.expanduser(
    os.environ.get("PHANTOM_SFX_OUT", "~/.local/share/omarchy/sounds/phantom-thieves")
)

# D minor, the pitch set these motifs are written from
D3, F3, A3, C4, D4, F4, A4, C5, D5, F5, A5 = (
    146.83, 174.61, 220.00, 261.63, 293.66, 349.23, 440.00, 523.25,
    587.33, 698.46, 1174.66,
)


# --------------------------------------------------------------- oscillators
def ns(dur):
    return max(1, int(SR * dur))


def sine(f, n, phase=0.0, amp=1.0):
    t = np.arange(n) / SR
    return amp * np.sin(2 * np.pi * f * t + phase)


def saw(f, n, harmonics=28, amp=1.0):
    """Additive saw -- band-limited so it never aliases."""
    t = np.arange(n) / SR
    out = np.zeros(n)
    for k in range(1, harmonics + 1):
        if f * k > SR * 0.45:
            break
        out += np.sin(2 * np.pi * f * k * t + phase_seed(k)) / k
    return amp * out * (2.0 / np.pi)


_phase_state = np.random.default_rng(11).random(64)


def phase_seed(k):
    return _phase_state[k % len(_phase_state)] * 0.0


def triangle(f, n, amp=1.0):
    t = (np.arange(n) / SR * f) % 1.0
    return amp * (4 * np.abs(t - 0.5) - 1.0)


def square(f, n, duty=0.5, amp=1.0, harmonics=24):
    t = np.arange(n) / SR
    out = np.zeros(n)
    for k in range(1, harmonics + 1):
        if f * k > SR * 0.45:
            break
        out += np.sin(2 * np.pi * f * k * t) * (2.0 / (k * np.pi)) * np.sin(np.pi * k * duty)
    return amp * out


def noise(n, rng, amp=1.0):
    return amp * rng.standard_normal(n)


# ------------------------------------------------------------------ envelopes
def decay(n, attack=0.002, tau=0.12, curve=3.0):
    a = max(1, int(SR * attack))
    env = np.exp(-np.arange(n) / (SR * tau))
    env[:a] *= np.linspace(0, 1, a)
    return env ** curve


def adsr(n, a=0.005, d=0.08, s=0.0, r=0.08):
    an, dn, rn = int(SR * a), int(SR * d), int(SR * r)
    out = np.concatenate([
        np.linspace(0, 1, max(an, 1)),
        np.linspace(1, s, max(dn, 1)),
        np.full(max(n - an - dn - rn, 0), s),
    ])
    if rn:
        out = np.concatenate([out[:max(len(out) - rn, 0)],
                              np.linspace(out[max(len(out) - rn - 1, 0)] if len(out) else s,
                                          0.0, rn)])
    return out[:n] if len(out) >= n else np.pad(out, (0, n - len(out)))


def sweep(f0, f1, n, curve=1.0, amp=1.0):
    t = np.arange(n) / SR
    k = np.linspace(0, 1, n) ** curve
    phase = 2 * np.pi * (f0 * t + (f1 - f0) * t ** 2 / 2)
    return amp * np.sin(phase)


# -------------------------------------------------------------------- filters
def _biquad(x, b, a):
    y = np.zeros_like(x)
    x1 = x2 = y1 = y2 = 0.0
    b0, b1, b2 = b
    a0, a1, a2 = a
    for i in range(len(x)):
        xi = x[i]
        yi = b0 * xi + b1 * x1 + b2 * x2 - a1 * y1 - a2 * y2
        y[i] = yi
        x2, x1 = x1, xi
        y2, y1 = y1, yi
    return y


def _rbj(kind, x, f0, q=0.707, gain=0.0):
    w0 = 2 * np.pi * f0 / SR
    cw, sw = math.cos(w0), math.sin(w0)
    alpha = sw / (2 * q)
    if kind == "lp":
        b = [(1 - cw) / 2, 1 - cw, (1 - cw) / 2]
        a = [1 + alpha, -2 * cw, 1 - alpha]
    elif kind == "hp":
        b = [(1 + cw) / 2, -(1 + cw), (1 + cw) / 2]
        a = [1 + alpha, -2 * cw, 1 - alpha]
    else:  # bandpass (constant peak)
        b = [alpha, 0.0, -alpha]
        a = [1 + alpha, -2 * cw, 1 - alpha]
    return _biquad(x, [v / a[0] for v in b], [v / a[0] for v in a])


def lowpass(x, f0, q=0.707):
    return _rbj("lp", x, f0, q)


def highpass(x, f0, q=0.707):
    return _rbj("hp", x, f0, q)


def bandpass(x, f0, q=2.0):
    return _rbj("bp", x, f0, q)


def lowpass_sweep(x, f_start, f_end, q=0.9):
    """Filter whose cutoff glides -- the 'open/close' gesture."""
    n = len(x)
    out = np.zeros(n)
    block = 256
    for i in range(0, n, block):
        seg = x[i:i + block]
        if len(seg) < 8:
            out[i:i + block] = seg
            continue
        p = (i + block / 2) / n
        f0 = f_start * (f_end / f_start) ** p
        out[i:i + block] = lowpass(seg, max(f0, 40.0), q)
    return out


# ------------------------------------------------------------------- effects
def softclip(x, drive=1.0):
    return np.tanh(x * drive) / np.tanh(drive) if drive > 0 else x


def delay_fx(x, time, feedback=0.3, mix=0.25, pingpong=False):
    d = int(SR * time)
    if d < 1:
        return x
    out = x.copy()
    acc = np.zeros(len(x) + d * 4)
    acc[:len(x)] += x
    step = d
    g = feedback
    for k in range(1, 5):
        off = step * k
        if off >= len(acc):
            break
        seg = acc[:len(x)]
        if pingpong and k % 2:
            seg = np.concatenate([np.zeros(off), seg[:len(x) - off]])
        acc[off:off + len(seg)] += seg * g
        g *= feedback
    return x * (1 - mix) + acc[:len(x)] * mix


def reverb(x, mix=0.2, decay=0.7, size=1.0):
    """Schroeder: four combs into two allpasses. Mono only."""
    combs = [(1557, 0.807), (1617, 0.803), (1491, 0.811), (1422, 0.815)]
    aps = [(225, 0.76), (556, 0.74)]
    wet = np.zeros(len(x) + int(SR * 0.4))
    for d, g in combs:
        d = int(d * size)
        b = np.zeros(len(wet))
        b[:len(x)] = x
        for i in range(d, len(wet)):
            b[i] += b[i - d] * (g * decay)
        wet += b
    wet /= len(combs)
    for d, g in aps:
        d = int(d * size)
        b = np.zeros(len(wet))
        b[:len(wet)] = wet
        for i in range(d, len(wet)):
            b[i] = -g * wet[i - d] + b[i - d] + g * b[i]
        wet = b
    wet = wet[:len(x)]
    return x * (1 - mix) + wet * mix


def pluck(freq, n, damp=0.5, bright=0.5, rng=None):
    """Karplus-Strong string -- the jazzy stab body."""
    rng = rng or np.random.default_rng(3)
    p = max(2, int(SR / freq))
    # Excitation: noise scaled by a mask. The mask must zero the excitation
    # outright -- offsetting it leaves a DC bias on every delay-line sample.
    exc = rng.uniform(-1.0, 1.0, p)
    exc *= (rng.random(p) < (0.35 + 0.5 * bright))
    exc -= exc.mean()
    buf = exc.copy()
    out = np.zeros(n)
    prev = 0.0
    for i in range(n):
        cur = buf[i % p]
        v = (cur + prev) * 0.5 * (0.996 - 0.004 * (1 - damp))
        out[i] = cur
        prev = cur
        buf[i % p] = v
    return out


def click(n=256, rng=None, tone=5200, q=1.2):
    """Transient attack -- the 'snap' Persona 5's UI sounds always have."""
    rng = rng or np.random.default_rng(7)
    x = noise(n, rng)
    x = bandpass(x, tone, q)
    x = highpass(x, 900)
    return x * decay(n, attack=0.0004, tau=0.004, curve=1.0)


# -------------------------------------------------------------------- voices
def stab(freqs, dur, tau=0.22, detune=0.006, gain=0.30, bright=0.55, damp=0.5):
    """A detuned chord stab."""
    n = ns(dur)
    rng = np.random.default_rng(int(freqs[0] * 7) % 9973)
    acc = np.zeros(n)
    for i, f in enumerate(freqs):
        for d in (-detune, 0.0, detune):
            acc += pluck(f * (1 + d), n, damp=damp, bright=bright, rng=rng) * (1 if d == 0 else 0.7)
    acc /= max(len(acc) / n, 1)
    acc = lowpass(acc, 3200 + 2600 * bright, 0.8)
    acc *= decay(n, attack=0.0015, tau=tau, curve=2.2)
    return acc * gain


def tone(freq, dur, wave_shape="sine", tau=0.15, gain=0.25, glide=None):
    n = ns(dur)
    if glide:
        x = sweep(freq, glide, n, amp=gain)
    else:
        x = {"sine": sine, "tri": triangle, "saw": saw, "square": square}[wave_shape](freq, n, amp=gain)
    x *= decay(n, attack=0.004, tau=tau, curve=2.0)
    return x


def thump(f0=110, f1=45, dur=0.22, gain=0.5):
    n = ns(dur)
    x = sweep(f0, f1, n, curve=1.4)
    x = lowpass(x, 320, 0.9)
    return x * decay(n, attack=0.001, tau=0.07, curve=1.6) * gain


def place(buf, x, at):
    i = int(at * SR)
    if i >= len(buf):
        return
    k = min(len(x), len(buf) - i)
    buf[i:i + k] += x[:k]


def dc_block(x, r=0.9995):
    """One-pole DC blocker. Safety net: a lowpass passes DC straight through,
    so any bias upstream would otherwise ride the whole file."""
    y = np.zeros_like(x)
    prev_x = 0.0
    prev_y = 0.0
    for i in range(len(x)):
        xi = x[i]
        yi = xi - prev_x + r * prev_y
        y[i] = yi
        prev_x, prev_y = xi, yi
    return y


def finish(mono, width_ms=7.0, verb_mix=0.16, drive=1.25, peak=0.86, out=None):
    """Stereoise, add a short room, tame the peaks, normalise."""
    d = int(SR * width_ms / 1000.0)
    left = np.pad(mono, (0, d))
    right = np.pad(mono, (d, 0))
    right = right * 0.97
    st = np.stack([left, right], axis=1)
    if verb_mix:
        # mono reverb kernel, applied per channel
        st = np.stack([reverb(st[:, c], mix=verb_mix, decay=0.62, size=0.9)
                       for c in range(st.shape[1])], axis=1)
    st = dc_block(st)
    st -= st.mean(axis=0, keepdims=True)
    st = softclip(st, drive)
    m = np.abs(st).max()
    if m > 0:
        st = st / m * peak
    st = np.clip(st, -1.0, 1.0)
    pcm = (st * 32767.0).astype(np.int16)
    path = out or "/dev/null"
    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    return path, len(pcm) / SR


# ------------------------------------------------------------------- designs
def s_workspace():
    """Switching desk: a dry tick with a short minor stab. Barely there."""
    n = ns(0.22)
    b = np.zeros(n)
    place(b, click(200) * 0.55, 0.0)
    place(b, stab([D4, F4, A4], 0.18, tau=0.07, gain=0.16, bright=0.7), 0.006)
    place(b, tone(D5, 0.06, "sine", tau=0.02, gain=0.10), 0.0)
    return b, dict(width_ms=4, verb_mix=0.07, drive=1.1)


def s_notify():
    """Two clean notes a fifth apart with a shimmer tail."""
    n = ns(0.75)
    b = np.zeros(n)
    place(b, stab([A4, C5], 0.3, tau=0.16, gain=0.17, bright=0.75), 0.0)
    place(b, stab([D5, A5], 0.34, tau=0.19, gain=0.14, bright=0.8), 0.085)
    place(b, tone(D5, 0.5, "sine", tau=0.22, gain=0.09), 0.085)
    place(b, tone(A5, 0.42, "sine", tau=0.16, gain=0.055), 0.10)
    place(b, click(160) * 0.28, 0.085)
    return b, dict(width_ms=9, verb_mix=0.22, drive=1.15)


def _menu_move_variant(freq, clickf, gain, tau):
    n = ns(0.035)
    b = np.zeros(n)
    place(b, click(clickf) * 0.13, 0.0)
    place(b, tone(freq, 0.028, "sine", tau=tau, gain=gain), 0.0)
    place(b, tone(freq * 0.75, 0.022, "sine", tau=tau * 0.8, gain=gain * 0.55), 0.004)
    return b, dict(width_ms=2, verb_mix=0.0, drive=1.0)


def s_menu_move_1():
    return _menu_move_variant(A5, 180, 0.10, 0.010)


def s_menu_move_2():
    # a shade lower and drier: the pair should read as the same blip, not two sounds
    return _menu_move_variant(F5, 200, 0.095, 0.008)


def s_menu_move_3():
    # brighter, shortest tail, so held-key repeat doesn't smear
    return _menu_move_variant(C5 * 2, 165, 0.105, 0.012)


def _menu_open_variant(f0, f1, f2, clickf, verb, wave="tri"):
    n = ns(0.14)
    b = np.zeros(n)
    place(b, click(clickf) * 0.30, 0.0)
    place(b, tone(f0, 0.11, wave, glide=f1, tau=0.035, gain=0.20), 0.0)
    place(b, tone(f2, 0.09, "sine", glide=f1 * 1.26, tau=0.03, gain=0.10), 0.012)
    return b, dict(width_ms=4, verb_mix=verb, drive=1.1)


def _menu_close_variant(f0, f1, clickf, verb, wave="tri"):
    n = ns(0.14)
    b = np.zeros(n)
    place(b, click(clickf) * 0.22, 0.0)
    place(b, tone(f0, 0.11, wave, glide=f1, tau=0.03, gain=0.19), 0.0)
    return b, dict(width_ms=4, verb_mix=verb, drive=1.1)


def s_menu_open_1():
    return _menu_open_variant(F4, C5, A4, 150, 0.08)


def s_menu_open_2():
    # starts a step higher, slightly wetter: same gesture, different lift
    return _menu_open_variant(A4, D5, C5, 165, 0.12)


def s_menu_open_3():
    # lowest and driest, sine body: reads as the "settled" variant
    return _menu_open_variant(D4, A4, F4, 140, 0.05, wave="sine")


def s_menu_close_1():
    return _menu_close_variant(C5, F4, 150, 0.08)


def s_menu_close_2():
    return _menu_close_variant(D5, F4, 165, 0.12)


def s_menu_close_3():
    # drops further and quieter, so closing never feels like a stab
    return _menu_close_variant(A4, D4, 140, 0.05, wave="sine")


def s_launch():
    """Launching something: stab over a body thump. The heaviest short sound."""
    n = ns(0.42)
    b = np.zeros(n)
    place(b, click(300) * 0.5, 0.0)
    place(b, thump(150, 48, 0.26, 0.55), 0.0)
    place(b, stab([D3, F3, A3, D4], 0.34, tau=0.13, gain=0.24, bright=0.6, damp=0.55), 0.004)
    place(b, tone(A4, 0.16, "saw", tau=0.06, gain=0.07), 0.0)
    return b, dict(width_ms=8, verb_mix=0.16, drive=1.45)


def s_lock():
    n = ns(0.6)
    b = np.zeros(n)
    place(b, tone(D4, 0.5, "saw", glide=A3, tau=0.20, gain=0.16), 0.0)
    x = noise(ns(0.5), np.random.default_rng(21))
    x = lowpass_sweep(x, 3000, 260, 0.9)
    x *= decay(len(x), attack=0.002, tau=0.16, curve=1.8)
    place(b, x * 0.16, 0.0)
    place(b, thump(120, 40, 0.3, 0.45), 0.005)
    return b, dict(width_ms=8, verb_mix=0.20, drive=1.3)


def s_unlock():
    n = ns(0.6)
    b = np.zeros(n)
    place(b, tone(A3, 0.4, "saw", glide=D4, tau=0.18, gain=0.15), 0.0)
    place(b, stab([D4, F4, A4, D5], 0.3, tau=0.12, gain=0.17, bright=0.65), 0.10)
    place(b, tone(F5, 0.2, "sine", tau=0.08, gain=0.07), 0.13)
    place(b, click(150) * 0.3, 0.10)
    return b, dict(width_ms=9, verb_mix=0.20, drive=1.25)


def s_error():
    """Tritone buzz -- deliberately uncomfortable, but short."""
    n = ns(0.34)
    b = np.zeros(n)
    place(b, tone(D4, 0.3, "square", tau=0.11, gain=0.13), 0.0)
    place(b, tone(A4 * 1.4142, 0.3, "square", tau=0.11, gain=0.11), 0.0)
    x = noise(ns(0.3), np.random.default_rng(33))
    x = bandpass(x, 1900, 1.1)
    x *= decay(len(x), attack=0.001, tau=0.07, curve=1.6)
    place(b, x * 0.14, 0.0)
    return b, dict(width_ms=3, verb_mix=0.05, drive=1.7)


def s_boot():
    """A short original sting: rising minor arpeggio into a held chord."""
    n = ns(2.0)
    b = np.zeros(n)
    seq = [(D3, 0.00), (F3, 0.11), (A3, 0.22), (D4, 0.33), (F4, 0.44), (A4, 0.55)]
    for f, at in seq:
        place(b, stab([f, f * 1.5], 0.5, tau=0.13, gain=0.13, bright=0.7), at)
    place(b, stab([D3, F3, A3, D4, F4, A4], 1.1, tau=0.5, gain=0.15, bright=0.6, damp=0.6), 0.70)
    place(b, tone(D4, 1.0, "tri", tau=0.42, gain=0.09), 0.70)
    place(b, tone(A4, 0.9, "sine", tau=0.36, gain=0.06), 0.72)
    place(b, click(240) * 0.4, 0.0)
    place(b, thump(130, 45, 0.35, 0.4), 0.0)
    return b, dict(width_ms=12, verb_mix=0.26, drive=1.35)


def _window_open_variant(f0, f1, f2, clickf, verb):
    # Heavier than menu-open: a low swell under a rising third, so opening an
    # app reads as "something launched" rather than "a panel appeared".
    n = ns(0.20)
    b = np.zeros(n)
    place(b, click(clickf) * 0.34, 0.0)
    place(b, tone(f0, 0.16, "tri", glide=f1, tau=0.055, gain=0.24), 0.0)
    place(b, tone(f2, 0.12, "sine", glide=f1 * 1.19, tau=0.045, gain=0.12), 0.016)
    place(b, tone(f0 / 2, 0.18, "sine", tau=0.07, gain=0.14), 0.0)
    return b, dict(width_ms=5, verb_mix=verb, drive=1.15)


def _window_close_variant(f0, f1, clickf, verb):
    # Falls further than menu-close and keeps the sub-octave weight, so a
    # closing window has a sense of mass going away.
    n = ns(0.20)
    b = np.zeros(n)
    place(b, click(clickf) * 0.24, 0.0)
    place(b, tone(f0, 0.16, "tri", glide=f1, tau=0.05, gain=0.22), 0.0)
    place(b, tone(f0 / 2, 0.19, "sine", tau=0.08, gain=0.15), 0.0)
    return b, dict(width_ms=5, verb_mix=verb, drive=1.15)


def s_window_open_1():
    return _window_open_variant(D4, A4, F4, 130, 0.14)


def s_window_open_2():
    return _window_open_variant(F4, C5, A4, 140, 0.17)


def s_window_open_3():
    return _window_open_variant(A3, F4, D4, 120, 0.11)


def s_window_close_1():
    return _window_close_variant(A4, D4, 130, 0.14)


def s_window_close_2():
    return _window_close_variant(C5, F4, 140, 0.17)


def s_window_close_3():
    return _window_close_variant(F4, A3, 120, 0.11)


def _menu_enter_variant(f1, f2, clickf, verb):
    # Committing to a row. Deliberately longer and wetter than the move tick
    # so "I moved" and "I went in" never blur together at a glance.
    n = ns(0.10)
    b = np.zeros(n)
    place(b, click(clickf) * 0.16, 0.0)
    place(b, tone(f1, 0.07, "tri", tau=0.026, gain=0.16), 0.0)
    place(b, tone(f2, 0.075, "sine", tau=0.030, gain=0.11), 0.022)
    return b, dict(width_ms=3, verb_mix=verb, drive=1.0)


def _menu_back_variant(f0, f1, clickf, verb):
    # Stepping back out. A soft fall, no upward motion, so it reads as retreat
    # rather than as another forward action.
    n = ns(0.09)
    b = np.zeros(n)
    place(b, click(clickf) * 0.12, 0.0)
    place(b, tone(f0, 0.065, "tri", glide=f1, tau=0.024, gain=0.15), 0.0)
    place(b, tone(f1, 0.05, "sine", tau=0.020, gain=0.08), 0.018)
    return b, dict(width_ms=3, verb_mix=verb, drive=1.0)


def s_menu_enter_1():
    return _menu_enter_variant(A4, C5 * 1.5, 150, 0.10)


def s_menu_enter_2():
    return _menu_enter_variant(C5, F5, 160, 0.13)


def s_menu_enter_3():
    return _menu_enter_variant(F4, A4, 140, 0.08)


def s_menu_back_1():
    return _menu_back_variant(D5, A4, 130, 0.10)


def s_menu_back_2():
    return _menu_back_variant(C5, F4, 140, 0.13)


def s_menu_back_3():
    return _menu_back_variant(A4, D4, 120, 0.08)


SET = {
    "workspace": s_workspace, "notify": s_notify,
    "window-open-1": s_window_open_1, "window-open-2": s_window_open_2,
    "window-open-3": s_window_open_3,
    "window-close-1": s_window_close_1, "window-close-2": s_window_close_2,
    "window-close-3": s_window_close_3,
    "menu-open-1": s_menu_open_1, "menu-open-2": s_menu_open_2,
    "menu-open-3": s_menu_open_3,
    "menu-close-1": s_menu_close_1, "menu-close-2": s_menu_close_2,
    "menu-close-3": s_menu_close_3,
    "menu-move-1": s_menu_move_1, "menu-move-2": s_menu_move_2,
    "menu-move-3": s_menu_move_3,
    "menu-enter-1": s_menu_enter_1, "menu-enter-2": s_menu_enter_2,
    "menu-enter-3": s_menu_enter_3,
    "menu-back-1": s_menu_back_1, "menu-back-2": s_menu_back_2,
    "menu-back-3": s_menu_back_3,
    "launch": s_launch,
    "lock": s_lock, "unlock": s_unlock, "error": s_error, "boot": s_boot,
}


def main():
    os.makedirs(OUT, exist_ok=True)
    only = os.sys.argv[1:]
    for name, fn in SET.items():
        if only and name not in only:
            continue
        buf, opts = fn()
        path, dur = finish(np.asarray(buf, dtype=float), out=os.path.join(OUT, name + ".wav"), **opts)
        print(f"  {name:12s} {dur:5.2f}s  {os.path.getsize(path) / 1024:6.1f}KB")


if __name__ == "__main__":
    main()
