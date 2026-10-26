"""Generate the Package Combo voice-over with edge-tts and place it on the timeline.

    pip install edge-tts
    python3 src/package_combo_vo.py              # writes assets/vo/*.mp3 + package-combo/src/vo.json
    python3 src/package_combo_vo.py --respell    # say "Study-olution" if the plain name sounds wrong

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
    (21, "05_royal", "Or claim the throne as Royal: five groups, two special price one-on-one sessions, and a performance report."),
    (26, "06_levels", "For every level: K S S R, K S S M, and international. Choose your path today."),
]


def duration(path):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path],
        capture_output=True, text=True, check=True,
    ).stdout
    return float(out.strip())


async def synth(text, rate, path):
    kw = {}
    proxy = os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy")
    if proxy:
        kw["proxy"] = proxy
    comm = edge_tts.Communicate(text, VOICE, rate=f"{rate:+d}%", pitch=PITCH, **kw)
    await comm.save(path)


async def main(respell):
    os.makedirs(VO_DIR, exist_ok=True)
    os.makedirs(PUB_VO, exist_ok=True)
    manifest, report, ok = [], [], True
    for i, (start, name, text) in enumerate(LINES):
        if respell:
            text = text.replace("Studyolution", "Study-olution")
        nxt = LINES[i + 1][0] if i + 1 < len(LINES) else END
        limit = nxt - start - GAP
        path = os.path.join(VO_DIR, f"{name}.mp3")
        rate = BASE_RATE
        await synth(text, rate, path)
        d = duration(path)
        while d > limit and rate < MAX_RATE:
            # jump close to the needed rate, then creep up 1% at a time
            need = int((1 + rate / 100) * d / limit * 100 - 100) + 1
            rate = min(MAX_RATE, max(rate + 1, need))
            await synth(text, rate, path)
            d = duration(path)
        fits = d <= limit
        ok &= fits
        shutil.copyfile(path, os.path.join(PUB_VO, f"{name}.mp3"))
        manifest.append({"file": f"{name}.mp3", "start": start, "duration": round(d, 3)})
        report.append(f"{start:>4.0f}s  {name:<11} {d:5.2f}s  (room {limit:4.2f}s, rate {rate:+d}%)"
                      + ("" if fits else "  ** STILL TOO LONG **"))
    with open(MANIFEST, "w") as f:
        json.dump(manifest, f, indent=1)
    print("\n".join(report))
    print("manifest:", MANIFEST)
    return 0 if ok else 2


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--respell", action="store_true", help='use "Study-olution" in the intro line')
    sys.exit(asyncio.run(main(ap.parse_args().respell)))
