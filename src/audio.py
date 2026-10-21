"""Synthesise the 8 s soundtrack: an upbeat 128 BPM loop plus whoosh / pop
effects timed to the animation. No samples, no voice-over.

    python3 src/audio.py build/audio.wav
"""
import sys

import numpy as np
from scipy.io import wavfile
from scipy.signal import butter, sosfilt

SR = 44100
DUR = 8.0
BPM = 128
BEAT = 60 / BPM
rng = np.random.default_rng(3)
N = int(SR * DUR)
t_all = np.arange(N) / SR


def env(n, a, d):
    """Attack/exponential-decay envelope over n samples (seconds)."""
    t = np.arange(n) / SR
    return np.minimum(1, t / max(a, 1e-4)) * np.exp(-t / d)


def place(buf, sig, at, gain=1.0):
    i = int(at * SR)
    if i >= len(buf):
        return
    sig = sig[: len(buf) - i]
    buf[i:i + len(sig)] += sig * gain


def kick():
    n = int(0.35 * SR)
    t = np.arange(n) / SR
    f = 48 + 110 * np.exp(-t * 28)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * env(n, 0.002, 0.12)


def clap():
    n = int(0.25 * SR)
    noise = rng.standard_normal(n)
    sos = butter(2, [900, 4500], "bandpass", fs=SR, output="sos")
    e = env(n, 0.001, 0.06) + 0.6 * np.concatenate([np.zeros(int(0.012 * SR)), env(n - int(0.012 * SR), 0.001, 0.05)])
    return sosfilt(sos, noise) * e


def hat(open_=False):
    n = int((0.22 if open_ else 0.06) * SR)
    sos = butter(4, 7000, "highpass", fs=SR, output="sos")
    return sosfilt(sos, rng.standard_normal(n)) * env(n, 0.001, 0.08 if open_ else 0.018)


def pluck(freq, dur=0.32, bright=1.0):
    n = int(dur * SR)
    t = np.arange(n) / SR
    s = sum(np.sin(2 * np.pi * freq * k * t) * (bright / k ** 1.3) for k in range(1, 7))
    return s * env(n, 0.003, 0.12) * 0.35


def saw_bass(freq, dur):
    n = int(dur * SR)
    t = np.arange(n) / SR
    s = 2 * ((freq * t) % 1) - 1
    sos = butter(2, 520, "lowpass", fs=SR, output="sos")
    return sosfilt(sos, s) * env(n, 0.004, dur * 0.9)


def pad(freqs, dur):
    n = int(dur * SR)
    t = np.arange(n) / SR
    s = sum(np.sin(2 * np.pi * f * t + 0.3 * np.sin(2 * np.pi * 0.4 * t)) for f in freqs)
    return s * np.minimum(1, t / 0.25) * np.minimum(1, (dur - t) / 0.3).clip(0) * 0.08


def whoosh(dur, f0, f1, gain=1.0):
    n = int(dur * SR)
    noise = rng.standard_normal(n)
    out = np.zeros(n)
    blocks = 48
    for b in range(blocks):
        a, z = b * n // blocks, (b + 1) * n // blocks
        fc = f0 * (f1 / f0) ** (b / blocks)
        sos = butter(2, [fc * 0.7, min(fc * 1.4, SR / 2 - 100)], "bandpass", fs=SR, output="sos")
        out[a:z] = sosfilt(sos, noise[max(0, a - 2000):z])[-(z - a):]
    x = np.linspace(0, 1, n)
    return out * np.sin(np.pi * x) ** 1.5 * gain


def pop(freq=520):
    n = int(0.12 * SR)
    t = np.arange(n) / SR
    f = freq * (1 + 1.6 * np.exp(-t * 60))
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * env(n, 0.001, 0.035)


def chime(freq):
    n = int(0.9 * SR)
    t = np.arange(n) / SR
    s = np.sin(2 * np.pi * freq * t) + 0.4 * np.sin(2 * np.pi * freq * 2.76 * t) * np.exp(-t * 6)
    return s * env(n, 0.002, 0.35)


def main(path):
    music = np.zeros(N)
    fx = np.zeros(N)

    # C - G - Am - F, one bar each
    roots = [130.81, 98.0, 110.0, 87.31]
    chords = [(261.63, 329.63, 392.0), (246.94, 293.66, 392.0), (261.63, 329.63, 440.0), (261.63, 349.23, 440.0)]
    beats = int(DUR / BEAT) + 1
    for b in range(beats):
        at = b * BEAT
        bar = (b // 4) % 4
        if b >= 1:  # let the first beat breathe under the opening whoosh
            place(music, kick(), at, 0.9)
        if b % 2 == 1:
            place(music, clap(), at, 0.35)
        place(music, hat(), at + BEAT / 2, 0.18)
        place(music, hat(b % 4 == 3), at + BEAT * 0.75, 0.08)
        place(music, saw_bass(roots[bar], BEAT * 0.45), at + BEAT * 0.5, 0.32)
        place(music, saw_bass(roots[bar] * (2 if b % 2 else 1), BEAT * 0.4), at, 0.22)
        arp = chords[bar]
        for k in range(2):
            place(music, pluck(arp[(b * 2 + k) % 3] * 2, bright=0.9), at + k * BEAT / 2, 0.22)
        if b % 4 == 0:
            place(music, pad(chords[bar], BEAT * 4), at, 1.0)

    # effects, timed to the picture
    place(fx, whoosh(0.9, 300, 5000), 0.0, 0.5)          # push-in + light sweep
    for at, f in ((2.0, 520), (2.38, 620), (2.76, 740)):  # Online / Class / Tutoring
        place(fx, whoosh(0.25, 2000, 600), at - 0.08, 0.25)
        place(fx, pop(f), at + 0.14, 0.6)
    place(fx, chime(1318.5), 2.95, 0.22)                   # ribbon shine
    place(fx, chime(1760.0), 3.2, 0.12)
    for at in (4.55, 4.95):                                # pins lift + drop
        place(fx, whoosh(0.22, 900, 3000), at, 0.18)
        place(fx, pop(330), at + 0.43, 0.7)
    place(fx, whoosh(0.5, 200, 1200), 6.0, 0.35)          # car
    place(fx, whoosh(0.6, 600, 4000), 6.3, 0.35)          # contact bar slides up
    place(fx, chime(2093.0), 6.95, 0.15)                   # bar shine
    place(fx, whoosh(0.6, 4000, 400), 6.8, 0.3)           # pull back to full poster
    place(fx, kick() + 0.5 * pad((261.63, 329.63, 392.0, 523.25), 1.0)[: len(kick())], 7.4, 0.8)

    mix = music * 0.75 + fx
    fade = np.ones(N)
    fade[: int(0.02 * SR)] = np.linspace(0, 1, int(0.02 * SR))
    tail = int(0.45 * SR)
    fade[-tail:] = np.linspace(1, 0, tail) ** 1.5
    mix *= fade
    mix = np.tanh(mix * 1.1) * 0.85
    mix /= max(1e-6, np.abs(mix).max()) / 0.89

    # light stereo: slightly delayed copy on the right
    d = int(0.011 * SR)
    right = np.concatenate([mix[:d] * 0.9, mix[:-d] * 0.15 + mix[d:] * 0.85])
    stereo = np.stack([mix, right], 1)
    wavfile.write(path, SR, (stereo * 32767).astype(np.int16))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "audio.wav")
