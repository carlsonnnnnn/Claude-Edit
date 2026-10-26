"""Synthesise the 30 s instrumental for the "Subjects Offered" video.

120 BPM, 4/4, D major, no vocals. Every sound is generated here (no samples).
The sections line up with the video timeline:

  0-3 s    airy pad + rising shimmer
  3-8 s    light pluck melody + soft claps (tutors appear); riser into 8 s
  8 s      punchy hit (title); 8-10 s short build into the groove
  10-25 s  main groove: bass, drums, hook melody; fills into 15 s and 20 s
  25-28 s  drums thin out, melody softens
  28-30 s  final D major chord rings out and ends at exactly 30.000 s

    python3 video/scripts/make_music.py
    -> out/subjects-offered-music.wav  (master, 44.1 kHz 16-bit stereo)
    -> assets/music.mp3                (320 kbps, picked up by prepare_assets.py)

Mastered to about -14 LUFS integrated with true peak at or below -1 dBTP.
"""
import os
import re
import subprocess
import tempfile

import numpy as np
from scipy.io import wavfile
from scipy.ndimage import minimum_filter1d
from scipy.signal import butter, fftconvolve, lfilter, resample_poly, sosfilt

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SR = 44100
DUR = 30.0
N = int(SR * DUR)
BPM = 120
BEAT = 60 / BPM  # 0.5 s; a 4/4 bar is 2 s
TARGET_LUFS = -14.0
CEILING_DBTP = -1.3  # headroom so the MP3 stays under -1 dBTP

rng = np.random.default_rng(7)


# ------------------------------------------------------------------ helpers --
def hz(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def tvec(dur):
    return np.arange(int(dur * SR)) / SR


def lp(x, f, order=2):
    return sosfilt(butter(order, f, "lowpass", fs=SR, output="sos"), x, axis=0)


def hp(x, f, order=2):
    return sosfilt(butter(order, f, "highpass", fs=SR, output="sos"), x, axis=0)


def bp(x, lo, hi, order=2):
    return sosfilt(butter(order, [lo, hi], "bandpass", fs=SR, output="sos"), x, axis=0)


def place(bus, sig, at, gain=1.0, pan=0.0):
    """Add a mono or stereo signal to a stereo bus at time `at` (constant-power pan)."""
    i = int(round(at * SR))
    if i >= len(bus):
        return
    if sig.ndim == 1:
        a = (pan + 1) * np.pi / 4
        sig = np.stack([sig * np.cos(a), sig * np.sin(a)], 1) * np.sqrt(2)
    sig = sig[: len(bus) - i]
    bus[i:i + len(sig)] += sig * gain


def automation(points):
    """Piecewise-linear gain curve over the whole track from (time, value) pairs."""
    ts, vs = zip(*points)
    return np.interp(np.arange(N) / SR, ts, vs)[:, None]


def saw(f, t, harmonics=None, phase=0.0):
    """Band-limited sawtooth (additive)."""
    k_max = int(min(harmonics or 60, (SR / 2 - 500) / f))
    out = np.zeros_like(t)
    for k in range(1, k_max + 1):
        out += np.sin(2 * np.pi * k * f * t + k * phase) / k
    return out * (2 / np.pi)


# -------------------------------------------------------------- instruments --
def pad_chord(notes, dur, attack=0.35, release=0.45, cutoff=2200):
    """Wide detuned-saw pad. Stereo."""
    t = tvec(dur + release)
    L = np.zeros_like(t)
    R = np.zeros_like(t)
    for m in notes:
        for d, side in ((-9, 0), (-3, 1), (4, 0), (10, 1), (0, 2)):
            f = hz(m) * 2 ** (d / 1200)
            v = saw(f, t, 24, phase=rng.uniform(0, 6.28))
            if side == 0:
                L += v
            elif side == 1:
                R += v
            else:
                L += v * 0.7
                R += v * 0.7
    env = np.minimum(1, t / attack) * np.clip((dur + release - t) / release, 0, 1)
    sig = np.stack([L, R], 1) * env[:, None]
    sig = lp(sig, cutoff, 2)
    return sig / (len(notes) * 3.2)


def pluck(m, dur=0.6, bright=1.0, decay=3.2):
    """Plucked synth: saw partials that decay faster the higher they are."""
    f = hz(m)
    t = tvec(dur)
    out = np.zeros_like(t)
    k_max = int(min(28, (SR / 2 - 500) / f))
    for k in range(1, k_max + 1):
        out += np.sin(2 * np.pi * k * f * t) / k * np.exp(-t * (decay + 2.2 * k / bright))
    out += 0.5 * np.sin(2 * np.pi * f * t) * np.exp(-t * decay * 0.7)  # body
    attack = np.minimum(1, t / 0.002)
    fade = np.clip((dur - t) / 0.03, 0, 1)
    return out * attack * fade * 0.5


def lead(m, dur):
    """Soft rounded lead that doubles the hook (triangle-ish)."""
    f = hz(m)
    t = tvec(dur + 0.08)
    s = sum(((-1) ** i) * np.sin(2 * np.pi * (2 * i + 1) * f * t) / (2 * i + 1) ** 2 for i in range(5))
    s += 0.25 * np.sin(2 * np.pi * 2 * f * t)
    vib = 1 + 0.004 * np.sin(2 * np.pi * 5.5 * t) * np.clip((t - 0.15) / 0.2, 0, 1)
    s = s * vib
    env = np.minimum(1, t / 0.012) * np.exp(-t * 1.2) * np.clip((dur + 0.08 - t) / 0.08, 0, 1)
    return s * env * 0.6


def bell(m, dur=1.6):
    f = hz(m)
    t = tvec(dur)
    s = (np.sin(2 * np.pi * f * t) * np.exp(-t * 2.2)
         + 0.35 * np.sin(2 * np.pi * f * 2.0 * t) * np.exp(-t * 3.5)
         + 0.18 * np.sin(2 * np.pi * f * 3.01 * t) * np.exp(-t * 6)
         + 0.08 * np.sin(2 * np.pi * f * 4.2 * t) * np.exp(-t * 9))
    return s * np.minimum(1, t / 0.003) * 0.5


def bass_note(m, dur, cutoff=700):
    f = hz(m)
    t = tvec(dur)
    s = saw(f, t, 30) * 0.55 + np.sin(2 * np.pi * f * t) * 0.9
    s = lp(s, cutoff, 2)
    env = np.minimum(1, t / 0.004) * np.exp(-t * 4.0) * np.clip((dur - t) / 0.02, 0, 1)
    return s * env


def kick(gain=1.0, length=0.42):
    t = tvec(length)
    f = 46 + 120 * np.exp(-t * 30)
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 7.5)
    click = lp(hp(rng.standard_normal(len(t)), 2500), 7000) * np.exp(-t * 300) * 0.12
    return (body + click) * gain


def clap(gain=1.0):
    t = tvec(0.3)
    noise = bp(rng.standard_normal(len(t)), 900, 5200)
    env = np.zeros_like(t)
    for off in (0.0, 0.009, 0.018):
        tt = np.clip(t - off, 0, None)
        env += (t >= off) * np.exp(-tt * 140) * 0.5
    env += (t >= 0.022) * np.exp(-np.clip(t - 0.022, 0, None) * 26)
    return noise * env * gain * 0.8


def hat(open_=False, gain=1.0):
    t = tvec(0.35 if open_ else 0.07)
    s = hp(rng.standard_normal(len(t)), 7500, 4)
    return s * np.exp(-t * (11 if open_ else 75)) * gain * 0.5


def snare(gain=1.0):
    t = tvec(0.22)
    tone = np.sin(2 * np.pi * 190 * t) * np.exp(-t * 30) * 0.6
    noise = bp(rng.standard_normal(len(t)), 1500, 8000) * np.exp(-t * 22)
    return (tone + noise) * gain * 0.7


def tom(m, gain=1.0):
    t = tvec(0.3)
    f = hz(m) * (1 + 0.5 * np.exp(-t * 25))
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 11) * gain


def crash(gain=1.0, length=2.2):
    t = tvec(length)
    s = hp(rng.standard_normal((len(t), 2)), 4500, 2)
    s = lp(s, 13000, 2)
    return s * np.exp(-t * 2.2)[:, None] * np.minimum(1, t / 0.002)[:, None] * gain * 0.35


def noise_riser(dur, f0, f1, gain=1.0, curve=2.0):
    """Filtered-noise sweep that grows to its end. Stereo."""
    n = int(dur * SR)
    noise = rng.standard_normal((n, 2))
    out = np.zeros((n, 2))
    blocks = 60
    for b in range(blocks):
        a, z = b * n // blocks, (b + 1) * n // blocks
        fc = f0 * (f1 / f0) ** (b / blocks)
        seg = bp(noise[max(0, a - 3000):z], fc * 0.6, min(fc * 1.6, SR / 2 - 200))
        out[a:z] = seg[-(z - a):]
    x = np.linspace(0, 1, n)
    return out * (x ** curve)[:, None] * gain


def tone_riser(dur, m0, m1, gain=1.0):
    t = tvec(dur)
    x = t / dur
    f = hz(m0) * (hz(m1) / hz(m0)) ** (x ** 1.5)
    ph = 2 * np.pi * np.cumsum(f) / SR
    s = np.sin(ph) + 0.3 * np.sin(2 * ph)
    return s * x ** 2.2 * gain


def impact(gain=1.0):
    """Punchy hit: deep boom + kick + noise burst. Stereo."""
    t = tvec(1.6)
    f = 38 + 90 * np.exp(-t * 12)
    boom = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 2.6)
    burst = lp(rng.standard_normal(len(t)), 2500) * np.exp(-t * 18) * 0.5
    mono = boom + burst
    k = kick(1.0)
    mono[: len(k)] += k * 0.8
    return np.stack([mono, mono], 1) * gain


# ----------------------------------------------------------------- effects --
def reverb_ir(rt=1.8, seed=3):
    r = np.random.default_rng(seed)
    t = tvec(rt * 1.4)
    decay = np.exp(-t * 6.9 / rt)
    ir = r.standard_normal((len(t), 2)) * decay[:, None]
    ir = lp(ir, 6000, 1)
    ir[: int(0.012 * SR)] *= np.linspace(0, 1, int(0.012 * SR))[:, None]
    return ir / np.sqrt((ir ** 2).sum(0))


def reverb(x, rt=1.8, seed=3):
    ir = reverb_ir(rt, seed)
    y = np.stack([fftconvolve(x[:, c], ir[:, c])[: len(x)] for c in range(2)], 1)
    return hp(y, 180, 1)


def pingpong(x, delay=0.375, fb=0.35, mix=1.0):
    d = int(delay * SR)
    y = np.zeros_like(x)
    src = x.copy()
    gain = 1.0
    for i in range(1, 6):
        gain *= fb
        side = (i % 2)
        shifted = np.zeros_like(x[:, 0])
        shifted[d * i:] = src[: len(x) - d * i].mean(1)
        y[:, side] += shifted * gain
    return lp(hp(y, 300, 1), 5000, 1) * mix


def sidechain(times, depth=0.55, release=0.16):
    g = np.ones(N)
    for at in times:
        i = int(at * SR)
        t = np.arange(N - i) / SR
        g[i:] *= 1 - depth * np.exp(-t / release)
    return g[:, None]


# ------------------------------------------------------------- arrangement --
def compose():
    pads = np.zeros((N, 2))
    keys = np.zeros((N, 2))   # plucks + lead
    bass = np.zeros((N, 2))
    drums = np.zeros((N, 2))
    fx = np.zeros((N, 2))
    shimmer = np.zeros((N, 2))
    final = np.zeros((N, 2))

    # Chords (I-V-vi-IV in D major), one per bar; G -> A turnaround into the drop.
    D, A, Bm, G = [62, 66, 69, 74], [61, 64, 69, 73], [62, 66, 71, 74], [62, 67, 71, 74]
    Asus = [62, 64, 69, 74]
    chords = [(0, D), (2, A), (4, Bm), (6, G), (8, G), (9, A),
              (10, D), (12, A), (14, Bm), (16, G), (18, D), (20, A), (22, Bm), (24, G),
              (26, Asus), (27, A)]
    for i, (at, notes) in enumerate(chords):
        end = chords[i + 1][0] if i + 1 < len(chords) else 28.0
        low = [notes[0] - 12] if at < 3 else []
        place(pads, pad_chord(low + notes, end - at, attack=1.2 if at == 0 else 0.25), at)
    pads *= automation([(0, 0.0), (0.2, 0.55), (3.0, 1.0), (3.5, 0.75), (8, 0.75), (8.05, 0.9),
                        (10, 0.55), (25, 0.55), (25.5, 0.8), (28, 0.8)])

    # 0-3 s: rising shimmer (bell arpeggio + airy noise swell).
    for k, m in enumerate([74, 78, 81, 86, 90, 93, 98, 102]):
        place(shimmer, bell(m, 1.4), 0.6 + k * 0.29, 0.18 + 0.03 * k, pan=-0.5 + k / 7)
    place(shimmer, noise_riser(3.0, 1500, 9000, curve=1.6), 0.0, 0.05)

    # 3-8 s: light pluck melody.
    intro = [(3.0, 69), (3.5, 73), (4.0, 74), (4.5, 78), (5.0, 83), (5.5, 78),
             (6.0, 79), (6.5, 74), (7.0, 71), (7.25, 74), (7.5, 76), (7.75, 78)]
    for at, m in intro:
        place(keys, pluck(m, 0.55, bright=0.8), at, 0.5, pan=0.15)
    # Soft claps on 2 and 4, a light shaker joins at 5 s.
    for at in (3.5, 4.5, 5.5, 6.5, 7.5):
        place(drums, clap(), at, 0.32, pan=0.05)
    for k in range(12):
        place(drums, hat(), 5.0 + k * 0.25, 0.10 + 0.04 * (k % 2), pan=0.35)

    # Riser into the 8 s title hit, then a short build into the 10 s drop.
    place(fx, noise_riser(1.5, 400, 8000, curve=1.2), 6.5, 0.45)
    place(fx, tone_riser(1.5, 50, 74), 6.5, 0.11)
    place(fx, impact(), 8.0, 0.75)
    place(fx, crash(), 8.0, 0.55)
    for m in G:
        place(keys, pluck(m, 0.9, bright=1.2, decay=2.0), 8.0, 0.32)
    place(keys, pluck(55, 0.9, bright=1.2, decay=2.0), 8.0, 0.32)
    for m in A:
        place(keys, pluck(m, 0.7, bright=1.0, decay=2.5), 9.0, 0.2)
    for k in range(8):  # snare build 9-10 s
        place(drums, snare(), 9.0 + k * 0.125, 0.10 + 0.06 * k)
    place(fx, noise_riser(1.0, 800, 10000, curve=2.5), 9.0, 0.12)

    # 10-25 s: main groove.
    kicks = []
    fills = {14.5: [(0, 50), (0.125, 47), (0.25, 45), (0.375, 43)],       # tom fill into 15 s
             19.5: [(0, 0), (0.125, 0), (0.25, 0), (0.375, 0)]}            # snare fill into 20 s
    for b in range(30):
        at = 10.0 + b * BEAT
        if at >= 25.0:
            break
        in_fill = any(f <= at < f + 0.5 for f in fills)
        if not in_fill:
            place(drums, kick(), at, 0.95)
            kicks.append(at)
        if b % 2 == 1 and not in_fill:
            place(drums, clap(), at, 0.42, pan=0.05)
        place(drums, hat(open_=(b % 4 == 3)), at + 0.25, 0.30 if b % 4 != 3 else 0.22, pan=0.3)
        place(drums, hat(), at + 0.125, 0.09, pan=0.3)
        place(drums, hat(), at + 0.375, 0.09, pan=0.3)
    for start, hits in fills.items():
        for off, m in hits:
            if m:
                place(drums, tom(m), start + off, 0.55, pan=0.3 - off)
            else:
                place(drums, snare(), start + off, 0.30 + off * 0.6)
    for at in (10.0, 15.0, 20.0):
        place(drums, crash(), at, 0.45)

    # Bouncy bass: root on the beat, octave on the off-beat.
    groove_roots = [(10, 38), (12, 33), (14, 35), (16, 31), (18, 38), (20, 33), (22, 35), (24, 31)]
    for bar_start, r in groove_roots:
        for e in range(8):
            at = bar_start + e * 0.25
            if at >= 25.0:
                break
            m = r if e % 2 == 0 else r + 12
            place(bass, bass_note(m, 0.22), at, 0.65 if e % 2 == 0 else 0.45)

    # Hook melody (eighth notes, None = rest/tie).
    hook = [
        [78, None, 81, 78, 76, 74, None, 76],   # D
        [76, None, 73, 76, 81, None, 78, 76],   # A
        [74, None, 78, 74, 83, None, 81, 78],   # Bm
        [79, None, 78, 76, 74, None, 76, 78],   # G
        [78, None, 81, 78, 76, 74, None, 76],   # D
        [76, None, 73, 76, 81, None, 83, 81],   # A
        [83, None, 81, 78, 83, None, 86, 83],   # Bm
        [81, None, 79, 78],                     # G (first half; softens at 25 s)
    ]
    for b, bar in enumerate(hook):
        for e, m in enumerate(bar):
            if m is None:
                continue
            length = 0.25
            j = e + 1
            while j < len(bar) and bar[j] is None:
                length += 0.25
                j += 1
            at = 10.0 + b * 2 + e * 0.25
            place(keys, pluck(m, length + 0.25, bright=1.1), at, 0.42, pan=-0.1)
            place(keys, lead(m, length * 0.9), at, 0.22, pan=0.1)

    # 25-28 s: thinner drums, softer melody, held bass.
    for k in range(6):
        at = 25.0 + k * 0.5
        place(drums, hat(), at + 0.25, 0.16 - 0.02 * k, pan=0.3)
        if k % 2 == 1 and at < 27:
            place(drums, clap(), at, 0.22 - 0.05 * k / 2)
    soft = [(25.0, 74, 0.5), (25.5, 71, 0.5), (26.0, 76, 0.5), (26.5, 74, 0.5), (27.0, 73, 0.5), (27.5, 76, 0.5)]
    for at, m, d in soft:
        place(keys, lp(pluck(m, 0.8, bright=0.6, decay=4), 2500), at, 0.34, pan=0.1)
    place(bass, bass_note(31, 1.0, 400) * np.linspace(1, 0.6, int(1.0 * SR)), 25.0, 0.5)
    place(bass, bass_note(33, 2.0, 400), 26.0, 0.45)

    # 28-30 s: final D major chord that rings out.
    big = [50, 57, 62, 66, 69, 74]
    place(final, pad_chord(big, 1.4, attack=0.03, release=0.6, cutoff=3200), 28.0, 1.0)
    for k, m in enumerate([62, 66, 69, 74, 78]):
        place(final, pluck(m, 2.0, bright=1.0, decay=1.6), 28.0 + k * 0.018, 0.33, pan=-0.4 + 0.2 * k)
    place(final, bell(86, 2.0), 28.02, 0.2)
    place(final, bell(93, 2.0), 28.05, 0.1, pan=0.3)
    place(final, bass_note(38, 2.0, 300), 28.0, 0.6)
    place(final, kick(0.8, 0.6), 28.0, 0.7)
    place(final, crash(0.8, 2.0), 28.0, 0.35)

    # Sidechain: pads and bass duck under every groove kick.
    sc = sidechain(kicks, depth=0.5)
    pads *= sc
    bass *= sidechain(kicks, depth=0.35, release=0.09)

    keys_wet = pingpong(keys, fb=0.3, mix=0.35)
    verb_in = pads * 0.25 + keys * 0.35 + shimmer * 0.9 + drums * 0.06 + final * 0.4 + fx * 0.15
    wet = reverb(verb_in, 2.2)

    mix = (pads * 0.55 + keys * 0.9 + keys_wet + bass * 0.9 + drums * 0.85
           + shimmer * 0.8 + fx * 0.8 + final * 0.9 + wet * 0.7)
    # Clean up lows below the bass and leave a slight mid dip for voice/SFX room.
    mix = hp(mix, 30, 2)
    return mix


# --------------------------------------------------------------- mastering --
def glue(x, thresh_db=-16, ratio=2.0, attack=0.01, release=0.15):
    """Gentle bus compressor on the stereo link."""
    level = np.abs(x).max(1)
    a_att = np.exp(-1 / (attack * SR))
    a_rel = np.exp(-1 / (release * SR))
    env = lfilter([1 - a_rel], [1, -a_rel], level)  # smooth level (release-dominated)
    env = np.maximum(env, lfilter([1 - a_att], [1, -a_att], level))
    db = 20 * np.log10(np.maximum(env, 1e-6))
    over = np.maximum(0, db - thresh_db)
    gain = 10 ** (-over * (1 - 1 / ratio) / 20)
    return x * gain[:, None]


def limit(x, ceiling_db, lookahead=0.004, release=0.08):
    """Look-ahead peak limiter driven by 4x-oversampled (true) peaks."""
    ceiling = 10 ** (ceiling_db / 20)
    up = np.abs(resample_poly(x, 4, 1, axis=0)).max(1)
    peak = up.reshape(-1, 4).max(1)[: len(x)]
    need = np.minimum(1.0, ceiling / np.maximum(peak, 1e-9))
    L = int(lookahead * SR)
    need = minimum_filter1d(need, size=2 * L + 1)
    # Smooth: instant down, exponential recovery.
    a = np.exp(-1 / (release * SR))
    g = np.empty_like(need)
    cur = 1.0
    for i, v in enumerate(need):
        cur = v if v < cur else cur * a + v * (1 - a)
        g[i] = cur
    g = np.convolve(g, np.ones(L) / L, mode="same")
    g = np.minimum(g, need)
    return x * g[:, None]


def measure(path):
    r = subprocess.run(["ffmpeg", "-nostats", "-i", path, "-af", "ebur128=peak=true", "-f", "null", "-"],
                       capture_output=True, text=True).stderr
    summary = r[r.rfind("Summary:"):]
    lufs = float(re.search(r"I:\s+(-?[\d.]+) LUFS", summary).group(1))
    tp = float(re.search(r"Peak:\s+(-?[\d.]+|-inf) dBFS", summary).group(1))
    return lufs, tp


def write_wav(path, x):
    wavfile.write(path, SR, (np.clip(x, -1, 1) * 32767).astype(np.int16))


def master(mix):
    mix = glue(mix)
    # Edges: 5 ms fade-in; the final chord is faded to silence by exactly 30 s.
    t = np.arange(N) / SR
    edge = np.minimum(1, t / 0.005)
    tail = np.clip((DUR - t) / 0.9, 0, 1)
    edge = edge * np.where(t > DUR - 0.9, 0.5 - 0.5 * np.cos(np.pi * tail), 1)
    mix = mix * edge[:, None]
    gain_db = 0.0
    tmp = os.path.join(tempfile.mkdtemp(), "m.wav")
    for _ in range(6):
        out = limit(mix * 10 ** (gain_db / 20), CEILING_DBTP)
        write_wav(tmp, out)
        lufs, tp = measure(tmp)
        print(f"  gain {gain_db:+.2f} dB -> {lufs:.2f} LUFS, true peak {tp:.2f} dBTP")
        if abs(lufs - TARGET_LUFS) < 0.15:
            break
        gain_db += TARGET_LUFS - lufs
    return out, lufs, tp


def main():
    os.makedirs(os.path.join(ROOT, "out"), exist_ok=True)
    mix = compose()
    peak = np.abs(mix).max()
    mix = mix / peak * 0.5
    out, lufs, tp = master(mix)
    wav = os.path.join(ROOT, "out", "subjects-offered-music.wav")
    write_wav(wav, out)
    mp3 = os.path.join(ROOT, "assets", "music.mp3")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", wav, "-c:a", "libmp3lame", "-b:a", "320k", mp3], check=True)
    print("wav", measure(wav), "mp3", measure(mp3))


if __name__ == "__main__":
    main()
