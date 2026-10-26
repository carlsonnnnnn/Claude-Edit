"""30 s royal fanfare bed (100 BPM, D major, no vocals).

Writes a MIDI score, renders it with FluidSynth (FluidR3 GM soundfont), then
EQs out a pocket for voice-over, normalises and trims to exactly 30.000 s.

    apt-get install fluidsynth fluid-soundfont-gm ffmpeg
    pip install mido
    python3 src/royal_music.py   # -> out/royal_fanfare_30s.wav / .mp3
"""
import os
import random
import subprocess

import mido

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUILD = os.path.join(ROOT, "build")
OUT = os.path.join(ROOT, "out")
SF2 = "/usr/share/sounds/sf2/FluidR3_GM.sf2"

TPB = 480
BPM = 100
B = 60 / BPM  # one beat = 0.6 s
SEC = TPB / B  # ticks per second (800)
random.seed(7)

# channel -> (bank, program, volume, pan)
CH = {
    "vln": (0, 48, 92, 50),     # strings (upper)
    "low": (0, 48, 88, 78),     # strings (lower)
    "timp": (0, 47, 110, 64),
    "harp": (0, 46, 80, 40),
    "tpt": (0, 56, 100, 58),
    "brass": (0, 61, 86, 70),
    "horn": (0, 60, 92, 82),
    "hpsi": (0, 6, 84, 38),
    "pizz": (0, 45, 100, 72),
    "perc": (128, 48, 100, 64),
    "tbn": (0, 57, 84, 88),
    "cb": (0, 43, 92, 76),
    "glock": (0, 9, 60, 30),
    "flute": (0, 73, 76, 36),
    "tuba": (0, 58, 80, 80),
}
CHAN = {}
for i, name in enumerate(n for n in CH if n != "perc"):
    CHAN[name] = i if i < 9 else i + 1
CHAN["perc"] = 9

events = []  # (tick, order, channel, msg)


def note(ch, t, dur, pitch, vel, human=True):
    if human:
        t += random.uniform(-0.006, 0.006)
        vel += random.randint(-4, 4)
    t = max(t, 0)
    vel = max(1, min(127, vel))
    c = CHAN[ch]
    events.append((round(t * SEC), 1, c, mido.Message("note_on", channel=c, note=pitch, velocity=vel)))
    events.append((round((t + dur) * SEC), 0, c, mido.Message("note_off", channel=c, note=pitch, velocity=0)))


def chord(ch, t, dur, pitches, vel, **kw):
    for p in pitches:
        note(ch, t, dur, p, vel, **kw)


def cc(ch, t, num, val):
    c = CHAN[ch]
    events.append((round(t * SEC), 0, c, mido.Message("control_change", channel=c, control=num, value=int(val))))


def ramp(ch, t0, t1, v0, v1, num=11, steps=24):
    for k in range(steps + 1):
        cc(ch, t0 + (t1 - t0) * k / steps, num, v0 + (v1 - v0) * k / steps)


def roll(ch, t0, t1, pitch, v0, v1, rate=0.06):
    n = int((t1 - t0) / rate)
    for k in range(n):
        note(ch, t0 + k * rate, rate * 1.5, pitch, int(v0 + (v1 - v0) * k / max(n - 1, 1)))


def arp(ch, t0, step, pitches, vel, dur=None):
    for k, p in enumerate(pitches):
        note(ch, t0 + k * step, dur or step * 4, p, vel)


# pitch names
def P(name):
    names = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}
    n = names[name[0]]
    rest = name[1:]
    if rest.startswith("#"):
        n += 1
        rest = rest[1:]
    elif rest.startswith("b"):
        n -= 1
        rest = rest[1:]
    return 12 * (int(rest) + 1) + n


def ps(s):
    return [P(x) for x in s.split()]


TIMP_D, TIMP_A = P("D2"), P("A1")
SNARE, CRASH, CRASH2, BASSD = 38, 49, 57, 36

# initial expression
for name in CH:
    cc(name, 0, 11, 100)
    cc(name, 0, 91, 70)  # reverb send
    cc(name, 0, 93, 0)   # no chorus

# ---------------------------------------------------------------- 0–3 s intro
ramp("vln", 0, 2.9, 35, 110)
ramp("low", 0, 2.9, 40, 110)
chord("low", 0.0, 3.05, ps("D2 D3 A3"), 70)
chord("vln", 0.0, 3.05, ps("F#4 A4 D5"), 62)
roll("timp", 0.1, 2.95, TIMP_D, 22, 70)
arp("harp", 0.25, 0.075, ps("D4 F#4 A4 D5 F#5 A5 D6 F#6"), 58)
arp("harp", 1.65, 0.075, ps("A4 D5 F#5 A5 D6 F#6 A6 D7"), 52)
note("glock", 2.4, 0.6, P("A6"), 40)

# ---------------------------------------------------------------- 3–6 s fanfare
cc("vln", 3.0, 11, 85)
cc("low", 3.0, 11, 90)
fan = [  # (t, dur, top, second)
    (3.0, 0.55, "D5", "A4"),
    (3.6, 0.19, "A4", "F#4"), (3.8, 0.19, "A4", "F#4"), (4.0, 0.19, "A4", "F#4"),
    (4.2, 0.28, "D5", "A4"), (4.5, 0.28, "F#5", "D5"),
    (4.8, 1.25, "A5", "F#5"),
]
for t, d, a, b in fan:
    v = 104 if d > 0.25 else 92
    note("tpt", t, d, P(a), v)
    note("tpt", t, d, P(b), v - 10)
chord("brass", 3.0, 0.55, ps("D3 A3 D4"), 92)
chord("brass", 4.8, 1.25, ps("D3 A3 D4"), 96)
chord("horn", 3.0, 0.55, ps("F#3 A3"), 84)
chord("horn", 4.8, 1.25, ps("F#3 A3"), 88)
note("tbn", 3.0, 0.55, P("D3"), 88)
note("tbn", 4.8, 1.25, P("D3"), 92)
note("tuba", 4.8, 1.25, P("D2"), 84)
for t, p, v in [(3.0, TIMP_D, 108), (4.2, TIMP_A, 90), (4.5, TIMP_A, 90), (4.8, TIMP_D, 112)]:
    note("timp", t, 0.6, p, v)
chord("low", 3.0, 3.0, ps("D2 D3"), 72)
chord("vln", 3.0, 3.0, ps("A4 D5"), 58)
ramp("brass", 5.3, 6.0, 100, 55)
ramp("tpt", 5.3, 6.0, 100, 50)
cc("brass", 6.05, 11, 100)
cc("tpt", 6.05, 11, 100)

# ---------------------------------------------------------------- 6–11 s scholarly
cc("vln", 6.0, 11, 70)
schol = [  # (start, chord tones low->high for harpsichord, pizz bass)
    (6.0, "D5 F#5 A5 D6", "D3 A2"),
    (7.2, "D5 G5 B5 D6", "G2 D3"),
    (8.4, "E5 G5 B5 E6", "E3 B2"),
    (9.6, "C#5 E5 A5 C#6", "A2 E3"),
]
for k, (t0, tones, bass) in enumerate(schol):
    tt = ps(tones)
    pattern = [0, 2, 1, 3, 2, 1, 3, 2]  # baroque broken chord, 16ths
    length = 1.4 if k == 3 else 1.2
    for i in range(int(length / 0.15)):
        note("hpsi", t0 + i * 0.15, 0.14, tt[pattern[i % 8]], 74 if i % 4 == 0 else 62)
    b = ps(bass)
    note("hpsi", t0, 0.55, b[0] + 12, 66)
    for i in range(int(length / B) + (1 if k == 3 else 0)):
        note("pizz", t0 + i * B, 0.3, b[i % 2], 88 if i % 2 == 0 else 74)
    # pizzicato violins on the off-beats
    for i in range(int(length / B)):
        note("pizz", t0 + i * B + 0.3, 0.2, tt[(i + 1) % 4], 60)
# little flute question-and-answer
for t, d, p in [(6.6, 0.3, "A5"), (6.9, 0.3, "B5"), (7.2, 0.6, "D6"),
                (8.7, 0.3, "G5"), (9.0, 0.3, "F#5"), (9.3, 0.3, "E5"), (9.6, 0.9, "A5")]:
    note("flute", t, d * 0.95, P(p), 68)
chord("low", 6.0, 4.9, ps("D2"), 45)
note("glock", 10.5, 0.4, P("A6"), 38)
note("timp", 10.7, 0.3, TIMP_A, 60)

# ---------------------------------------------------------------- 11–16 s march
march = [  # 16th-note snare pattern per beat; 1 = hit, 2 = accent
    [2, 0, 1, 1], [2, 0, 1, 0], [2, 0, 1, 1], [2, 1, 1, 1],
]


def snare_bar(t0, nbeats, scale=1.0):
    for bt in range(nbeats):
        pat = march[bt % 4]
        for s, h in enumerate(pat):
            if h:
                note("perc", t0 + bt * B + s * B / 4, 0.1, SNARE, int((96 if h == 2 else 66) * scale))


snare_bar(11.0, 8)
for bt in range(0, 8, 2):
    note("perc", 11.0 + bt * B, 0.4, BASSD, 70)
horn_mel = [  # noble horn tune
    (11.0, 0.9, "D4"), (11.9, 0.3, "E4"), (12.2, 0.6, "F#4"), (12.8, 0.6, "D4"),
    (13.4, 0.9, "G4"), (14.3, 0.3, "F#4"), (14.6, 0.6, "E4"), (15.2, 0.75, "A4"),
]
for t, d, p in horn_mel:
    note("horn", t, d * 0.97, P(p), 98)
    note("horn", t, d * 0.97, P(p) - 12, 84)
march_ch = [(11.0, "D2", "D3 A3"), (12.2, "B1", "B2 F#3"), (13.4, "G1", "G2 D3"), (14.6, "A1", "A2 E3")]
for k, (t0, bass, low) in enumerate(march_ch):
    length = 1.4 if k == 3 else 1.2
    for i in range(int(round(length / B))):
        note("pizz", t0 + i * B, 0.3, P(bass) + 12, 84)
    chord("low", t0, length, ps(low), 66)
    note("cb", t0, length, P(bass), 74)
    note("timp", t0, 0.5, TIMP_D if k % 2 == 0 else TIMP_A, 84)
chord("tpt", 15.2, 0.75, ps("C#5 E5"), 70)
cc("low", 11.0, 11, 85)

# ---------------------------------------------------------------- 16–21 s strings swell
ramp("vln", 16.0, 20.8, 55, 120)
ramp("low", 16.0, 20.8, 60, 120)
swell = [  # (t, dur, violins high, low strings, bass)
    (16.0, 1.2, "B4 D5 G5", "G2 D3 B3", "G1"),
    (17.2, 1.2, "A4 D5 F#5", "F#2 D3 A3", "F#1"),
    (18.4, 1.2, "G4 B4 E5", "E2 B2 G3", "E1"),
    (19.6, 0.7, "A4 D5 E5", "A2 E3 A3", "A1"),
    (20.3, 0.75, "A4 C#5 E5", "A2 E3 A3", "A1"),
]
for t, d, hi, lo, bs in swell:
    chord("vln", t, d + 0.02, ps(hi), 84)
    chord("low", t, d + 0.02, ps(lo), 80)
    note("cb", t, d, P(bs) + 12, 80)
vln_mel = [  # elegant soaring line over the chords
    (16.0, 0.9, "D6"), (16.9, 0.3, "B5"), (17.2, 0.9, "A5"), (18.1, 0.3, "F#5"),
    (18.4, 0.6, "G5"), (19.0, 0.6, "B5"), (19.6, 0.7, "A5"), (20.3, 0.7, "C#6"),
]
for t, d, p in vln_mel:
    note("vln", t, d * 0.98, P(p), 92)
for k, t in enumerate([16.0, 17.2, 18.4]):
    arp("harp", t, 0.1, [x + (0 if k else 0) for x in
                         (ps("G3 D4 G4 B4 D5 G5"), ps("F#3 D4 F#4 A4 D5 F#5"), ps("E3 B3 E4 G4 B4 E5"))[k]], 50)
chord("horn", 18.4, 2.6, ps("B3 E4"), 60)
ramp("horn", 18.4, 20.9, 60, 110)
roll("perc", 20.0, 20.98, SNARE, 40, 100, rate=0.05)
roll("timp", 20.3, 20.98, TIMP_A, 50, 105, rate=0.05)

# ---------------------------------------------------------------- 21–26 s climax
for n in ("vln", "low", "horn", "brass", "tpt", "tbn", "tuba"):
    cc(n, 21.0, 11, 100)
note("perc", 21.0, 2.5, CRASH, 110, human=False)
note("perc", 21.0, 2.5, CRASH2, 110, human=False)
note("perc", 21.0, 0.5, BASSD, 110)
note("glock", 21.0, 1.0, P("D7"), 70)
clim = [  # (t, dur, chord brass mid, bass)
    (21.0, 1.2, "D3 A3 D4 F#4", "D1"),
    (22.2, 1.2, "D3 G3 B3 D4", "G1"),
    (23.4, 0.6, "D3 F#3 B3 D4", "B1"),
    (24.0, 0.6, "D3 G3 B3 D4", "G1"),
    (24.6, 0.6, "D3 A3 D4 E4", "A1"),
    (25.2, 0.8, "C#3 G3 A3 E4", "A1"),
]
for t, d, br, bs in clim:
    chord("brass", t, d * 0.96, ps(br), 98)
    note("tbn", t, d * 0.96, ps(br)[0], 92)
    note("tuba", t, d * 0.96, P(bs) + 12, 92)
    note("cb", t, d, P(bs) + 12, 96)
    chord("low", t, d, [P(bs) + 12, P(bs) + 24], 92)
fan2 = [  # bigger fanfare reprise, top + harmony a 3rd/6th below
    (21.0, 0.55, "D5", "A4"),
    (21.6, 0.19, "A4", "F#4"), (21.8, 0.19, "A4", "F#4"), (22.0, 0.19, "A4", "F#4"),
    (22.2, 0.28, "D5", "B4"), (22.5, 0.28, "G5", "D5"),
    (22.8, 0.58, "B5", "G5"),
    (23.4, 0.58, "B5", "F#5"), (24.0, 0.28, "A5", "F#5"), (24.3, 0.28, "G5", "D5"),
    (24.6, 0.28, "F#5", "D5"), (24.9, 0.28, "E5", "C#5"),
    (25.2, 0.38, "E5", "C#5"), (25.6, 0.18, "C#5", "A4"), (25.8, 0.18, "E5", "C#5"),
]
for t, d, a, b in fan2:
    v = 116 if d > 0.25 else 102
    note("tpt", t, d, P(a), v)
    note("tpt", t, d, P(b), v - 12)
# violins drive with repeated 8ths an octave up, high and out of the voice band
for i in range(int(5.0 / 0.3)):
    t = 21.0 + i * 0.3
    top = [ps("D6 A6"), ps("D6 G6"), ps("D6 B6")][0 if t < 22.2 else 1 if t < 23.4 else 2 if t < 24.0 else 1]
    if t >= 24.6:
        top = ps("E6 A6") if t < 25.2 else ps("E6 C#6")
    chord("vln", t, 0.27, top, 84 if i % 2 == 0 else 70)
for t, p, v in [(21.0, TIMP_D, 120), (22.2, TIMP_D, 108), (23.4, TIMP_A, 104), (24.0, TIMP_D, 104), (24.6, TIMP_A, 110)]:
    note("timp", t, 0.6, p, v)
roll("timp", 25.2, 25.98, TIMP_A, 70, 118, rate=0.045)
snare_bar(21.0, 7, scale=0.95)
roll("perc", 25.2, 25.98, SNARE, 60, 112, rate=0.045)
horn_ctr = [(21.0, 1.2, "F#4"), (22.2, 1.2, "G4"), (23.4, 0.6, "F#4"), (24.0, 0.6, "G4"), (24.6, 0.6, "A4"), (25.2, 0.8, "A4")]
for t, d, p in horn_ctr:
    note("horn", t, d * 0.97, P(p), 104)
    note("horn", t, d * 0.97, P(p) - 12, 94)

# ---------------------------------------------------------------- 26–30 s final chord
for n in ("vln", "low", "horn", "brass", "tpt", "tbn", "tuba", "cb", "harp"):
    cc(n, 26.0, 11, 100)
    ramp(n, 26.6, 29.0, 100, 25)
END = 3.0  # notes stop at 29.0; reverb tail fades to silence by 30.0
note("perc", 26.0, 2.0, CRASH, 96, human=False)
note("perc", 26.0, 0.5, BASSD, 110)
chord("tpt", 26.0, END, ps("D5 F#5 A5"), 112)
chord("brass", 26.0, END, ps("D3 A3 D4"), 100)
chord("horn", 26.0, END, ps("F#3 D4"), 96)
note("tbn", 26.0, END, P("D3"), 96)
note("tuba", 26.0, END, P("D2"), 96)
note("cb", 26.0, END, P("D2"), 100)
chord("low", 26.0, END, ps("D2 A2 D3"), 96)
chord("vln", 26.0, END, ps("A5 D6 F#6"), 92)
note("timp", 26.0, 0.8, TIMP_D, 124)
roll("timp", 26.9, 28.6, TIMP_D, 70, 25, rate=0.06)
arp("harp", 26.05, 0.06, ps("D3 A3 D4 F#4 A4 D5 F#5 A5 D6"), 70, dur=2.4)
note("glock", 26.0, 2.0, P("D7"), 66)
note("glock", 26.0, 2.0, P("A6"), 56)

# ---------------------------------------------------------------- write MIDI
mid = mido.MidiFile(ticks_per_beat=TPB)
track = mido.MidiTrack()
mid.tracks.append(track)
track.append(mido.MetaMessage("set_tempo", tempo=mido.bpm2tempo(BPM), time=0))
track.append(mido.MetaMessage("time_signature", numerator=4, denominator=4, time=0))
for name, (bank, prog, vol, pan) in CH.items():
    c = CHAN[name]
    track.append(mido.Message("control_change", channel=c, control=0, value=0, time=0))
    track.append(mido.Message("control_change", channel=c, control=32, value=0, time=0))
    track.append(mido.Message("program_change", channel=c, program=prog, time=0))
    track.append(mido.Message("control_change", channel=c, control=7, value=vol, time=0))
    track.append(mido.Message("control_change", channel=c, control=10, value=pan, time=0))
events.sort(key=lambda e: (e[0], e[1]))
now = 0
for tick, _, _, msg in events:
    track.append(msg.copy(time=tick - now))
    now = tick

os.makedirs(BUILD, exist_ok=True)
os.makedirs(OUT, exist_ok=True)
midi_path = os.path.join(BUILD, "royal_fanfare.mid")
raw_path = os.path.join(BUILD, "royal_fanfare_raw.wav")
mid.save(midi_path)
print("midi:", midi_path)

# ---------------------------------------------------------------- render + master
subprocess.run([
    "fluidsynth", "-ni", "-q", "-r", "48000", "-g", "0.45",
    "-o", "synth.reverb.room-size=0.78", "-o", "synth.reverb.damp=0.35",
    "-o", "synth.reverb.width=1.0", "-o", "synth.reverb.level=0.75",
    "-o", "synth.chorus.active=0",
    "-F", raw_path, SF2, midi_path,
], check=True)

# Voice-over pocket: gentle dips at the body (~350 Hz) and presence (~2.5 kHz)
# bands, a touch of air on top, rumble cut, then loudness normalisation.
eq = ",".join([
    "highpass=f=32",
    "equalizer=f=350:t=q:w=1.0:g=-2.5",
    "equalizer=f=1200:t=q:w=1.2:g=-2",
    "equalizer=f=2600:t=q:w=1.0:g=-4",
    "highshelf=f=8000:g=1.5",
    "apad=whole_dur=30",
    "atrim=0:30",
])
eq_path = os.path.join(BUILD, "royal_fanfare_eq.wav")
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", raw_path, "-af", eq,
                "-c:a", "pcm_f32le", eq_path], check=True)

# two-pass loudness: measure, then a static gain to -16 LUFS behind a limiter
meas = subprocess.run(["ffmpeg", "-hide_banner", "-i", eq_path, "-af", "ebur128", "-f", "null", "-"],
                      capture_output=True, text=True).stderr
lufs = float(meas.rsplit("I:", 1)[1].split("LUFS")[0])
gain = -16.0 - lufs
master = ",".join([
    f"volume={gain:.2f}dB",
    "alimiter=limit=0.84:attack=3:release=60:level=disabled",
    "afade=t=in:st=0:d=0.05",
    "afade=t=out:st=28.6:d=1.4:curve=exp",
    "atrim=0:30",
])
wav = os.path.join(OUT, "royal_fanfare_30s.wav")
mp3 = os.path.join(OUT, "royal_fanfare_30s.mp3")
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", eq_path, "-af", master,
                "-ar", "48000", "-c:a", "pcm_s24le", wav], check=True)
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", wav, "-c:a", "libmp3lame", "-b:a", "320k", mp3], check=True)
print(f"measured {lufs:.1f} LUFS, gain {gain:+.1f} dB")
print("out:", wav, mp3)
