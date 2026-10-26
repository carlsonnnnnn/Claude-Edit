"""Generate the Package Combo voice-over with edge-tts and place it on the timeline.

    pip install edge-tts
    python3 src/package_combo_vo.py              # writes assets/vo/*.mp3 + package-combo/src/vo.json
    python3 src/package_combo_vo.py --respell    # say "Study-olution" if the plain name sounds wrong
    python3 src/package_combo_vo.py --lang bm    # Bahasa Malaysia -> assets/vo/bm/ + package-combo/src/vo_bm.json

Each clip must end before the next line starts. A clip that runs long is regenerated
for that line only at a faster rate, never above +10%.
"""
import argparse
import asyncio
import json
import os
import shutil
import subprocess
import sys

import edge_tts
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VO_DIR = os.path.join(ROOT, "assets", "vo")
PUB_VO = os.path.join(ROOT, "package-combo", "public", "vo")
MANIFEST = os.path.join(ROOT, "package-combo", "src", "vo.json")

VOICE = "en-GB-RyanNeural"
BASE_RATE = -5
MAX_RATE = 10
PITCH = "-2Hz"
END = 30.0
GAP = 0.15  # breathing room before the next line

LINES = [
    (0, "01_intro", "Every great kingdom is built on knowledge. Welcome to Studyolution Academy's Package Combo."),
    (6, "02_scholar", "Begin as a Scholar: one subject group, with free notes and exercises."),
    (11, "03_knight", "Rise as a Knight: three subject groups, ten percent off."),
    (16, "04_noble", "Advance as a Noble: five subject groups, fifteen percent off."),
    # Shortened from the brief: the full lines need ~12.3 s between 21 s and 30 s even at +10%.
    (21, "05_royal", "Claim the throne as Royal: special price one-on-ones and a performance report."),
    (26, "06_levels", "For every level. Choose your path today."),
]

# Bahasa Malaysia (ms-MY, not Indonesian): peratus, diskaun, percuma, laluan, peringkat.
# Package names stay in English to match the screen.
LINES_BM = [
    (0, "01_intro", "Kerajaan agung dibina atas ilmu. Selamat datang ke Pakej Kombo Studyolution Academy."),
    (6, "02_scholar", "Mulakan sebagai Scholar: satu kumpulan subjek, dengan nota dan latihan percuma."),
    (11, "03_knight", "Bangkit sebagai Knight: tiga kumpulan subjek, diskaun sepuluh peratus."),
    (16, "04_noble", "Maju sebagai Noble: lima kumpulan subjek, diskaun lima belas peratus."),
    (21, "05_royal", "Jadilah Royal: sesi individu harga istimewa dan laporan prestasi."),
    (26, "06_levels", "Untuk semua peringkat. Pilih laluan anda hari ini."),
]

LANGS = {
    "en": dict(voice=VOICE, lines=LINES, vo_dir=VO_DIR, pub=PUB_VO, manifest=MANIFEST),
    "bm": dict(voice="ms-MY-OsmanNeural", lines=LINES_BM, vo_dir=os.path.join(VO_DIR, "bm"),
               pub=os.path.join(ROOT, "package-combo", "public", "vo_bm"),
               manifest=os.path.join(ROOT, "package-combo", "src", "vo_bm.json")),
}


def duration(path):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path],
        capture_output=True, text=True, check=True,
    ).stdout
    return float(out.strip())


LEAD_PAD = 0.05  # s of silence kept before / after the speech
TAIL_PAD = 0.15


def trim_silence(path):
    """edge-tts pads clips with ~0.2 s before and ~0.8 s after the speech; cut that down."""
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-f", "f32le", "-ac", "1", "-ar", "24000", "-"],
                         capture_output=True, check=True).stdout
    x = np.frombuffer(raw, np.float32)
    loud = np.nonzero(np.abs(x) > 0.003)[0]
    t0 = max(0.0, loud[0] / 24000 - LEAD_PAD)
    t1 = min(len(x) / 24000, loud[-1] / 24000 + TAIL_PAD)
    tmp = path + ".tmp.mp3"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{t0:.3f}", "-to", f"{t1:.3f}", "-i", path,
                    "-af", "afade=t=out:st=%.3f:d=0.08" % (t1 - t0 - 0.08), "-c:a", "libmp3lame", "-b:a", "96k", tmp],
                   check=True)
    os.replace(tmp, path)
    # edge-tts comes out around -21 dB; bring speech to -16 LUFS so it clears the ducked music
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", path, "-af", "loudnorm=I=-16:TP=-1.5:LRA=7,aresample=24000",
                    "-c:a", "libmp3lame", "-b:a", "96k", tmp], check=True)
    os.replace(tmp, path)


async def synth(text, rate, path, voice=VOICE):
    kw = {}
    proxy = os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy")
    if proxy:
        kw["proxy"] = proxy
    comm = edge_tts.Communicate(text, voice, rate=f"{rate:+d}%", pitch=PITCH, **kw)
    await comm.save(path)
    trim_silence(path)


async def main(respell, lang):
    cfg = LANGS[lang]
    lines = cfg["lines"]
    os.makedirs(cfg["vo_dir"], exist_ok=True)
    os.makedirs(cfg["pub"], exist_ok=True)
    manifest, report, ok = [], [], True
    for i, (start, name, text) in enumerate(lines):
        if respell:
            text = text.replace("Studyolution", "Study-olution")
        nxt = lines[i + 1][0] if i + 1 < len(lines) else END
        limit = nxt - start - GAP
        path = os.path.join(cfg["vo_dir"], f"{name}.mp3")
        rate = BASE_RATE
        await synth(text, rate, path, cfg["voice"])
        d = duration(path)
        while d > limit and rate < MAX_RATE:
            # jump close to the needed rate, then creep up 1% at a time
            need = int((1 + rate / 100) * d / limit * 100 - 100) + 1
            rate = min(MAX_RATE, max(rate + 1, need))
            await synth(text, rate, path, cfg["voice"])
            d = duration(path)
        fits = d <= limit
        ok &= fits
        shutil.copyfile(path, os.path.join(cfg["pub"], f"{name}.mp3"))
        manifest.append({"file": f"{name}.mp3", "start": start, "duration": round(d, 3)})
        report.append(f"{start:>4.0f}s  {name:<11} {d:5.2f}s  (room {limit:4.2f}s, rate {rate:+d}%)"
                      + ("" if fits else "  ** STILL TOO LONG **"))
    with open(cfg["manifest"], "w") as f:
        json.dump(manifest, f, indent=1)
    print("\n".join(report))
    print("manifest:", cfg["manifest"])
    return 0 if ok else 2


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--respell", action="store_true", help='use "Study-olution" in the intro line')
    ap.add_argument("--lang", choices=sorted(LANGS), default="en", help="en (default) or bm (Bahasa Malaysia)")
    args = ap.parse_args()
    sys.exit(asyncio.run(main(args.respell, args.lang)))
