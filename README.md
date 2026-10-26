# Studyolution Academy – animated poster

`out/studyolution_promo.mp4` is an 8 s, 1080×1920 (9:16), 30 fps H.264 video with AAC audio, made from `assets/poster.png`.

Every moving part is cut from the original poster pixels, so no text, face, glasses, suit or name tag is ever redrawn. Frame 0 and the final hold (7.4–8 s) match the poster exactly. The poster is 3:4, so it sits in the middle of the 9:16 frame and the blue grid continues above and below it.

| Time | What moves |
|---|---|
| 0–2 s | Slow push-in, light sweep and grid shimmer. Cubes, ÷ and + float, the big atom sways, the small atom spins, stars twinkle. |
| 2–4 s | "Online", "Class" and "Tutoring" bounce in turn. A light runs along the "With Sir Isaac Carlson" ribbon. |
| 4–6 s | The three figures lift or lean slightly. The green pins lift and drop onto the notes. The Ag and Br tiles bob. |
| 6–8 s | The car rolls back and drives into place on the K.E ramp, the DNA helix turns, the contact bar slides up, then the camera pulls back and holds on the full poster. |

Audio is generated in code (`src/audio.py`): a 128 BPM loop with whoosh, pop and chime effects. There is no voice-over.

## Rebuild

```
pip install opencv-python-headless scipy numpy
python3 src/layers.py   # cut-outs and clean background plates -> build/
python3 src/render.py   # video -> out/studyolution_promo.mp4
python3 src/render.py --stills   # preview frames -> build/stills/
```

## Royal fanfare music bed

`out/royal_fanfare_30s.wav` (24-bit 48 kHz) and `.mp3` are a 30 s instrumental for a royal-themed promo: D major, 100 BPM, no vocals. It moves from an intro (0–3 s) to a brass fanfare (3–6 s), harpsichord and pizzicato (6–11 s), a march (11–16 s), a string swell (16–21 s), the climax with a cymbal hit at 21 s (21–26 s) and a final chord that is silent by 30 s. The mix leaves a pocket in the mid-range for voice-over, at about -16 LUFS.

```
apt-get install fluidsynth fluid-soundfont-gm ffmpeg
pip install mido
python3 src/royal_music.py   # MIDI -> build/, audio -> out/
```

## Package Combo – 30 s Remotion video

`out/package-combo-30s.mp4` is 1080×1440, 30 fps, 900 frames, H.264 + AAC, built in Remotion (React + TypeScript) from `assets/package-combo/poster.png`. `out/final-frame.png` is frame 899, which holds on the poster layout. The one text change: the Royal row's third cell reads "+ 15% off + academic performance report + special price 1-on-1 sessions".

| Time | Section (`package-combo/src/sections/`) |
|---|---|
| 0–3 s | `Background`, `GoldDust`, `Intro`: navy grid plate fades in, gold dust drifts up, logo and name fade in |
| 3–6 s | `Title`: "Package Combo" bounces in, gold shine sweep; `Table` cell borders draw |
| 6–26 s | `Table` rows slide in cell by cell; `Characters` rise in: scholar (warm glow), knight (metallic glint, "10%" pops), prince (crown sparkle), king (gold burst behind the throne, gold pulse on the Royal row) |
| 26–28 s | `Finale` → `AvailableCard`: white card slides up, the four levels appear one by one |
| 28–30 s | `Finale` → `ContactBar`: bar slides up, icons pop in, hold |

The table and title text use League Spartan Bold, which matches the poster more closely than Poppins. The header is cut from the poster; the card and contact bar contents are cut from the poster too, so their text is pixel-exact. Characters are cut out of the painting, and they only rise, drift slightly and get light effects.

Audio (`AudioMix.tsx`): `royal_fanfare_30s.mp3` (copied into `public/`) at full level, ducked to 30% under each voice line, faded out over the last second. Voice-over clips are read from `package-combo/src/vo.json`, which `src/package_combo_vo.py` writes. The voice is edge-tts `en-GB-RyanNeural` at pitch -2Hz. The script trims edge-tts's padding silence and normalises each clip to -16 LUFS.

| Start | Line | Length | Rate |
|---|---|---|---|
| 0 s | Every great kingdom is built on knowledge. Welcome to Studyolution Academy's Package Combo. | 5.78 s | +1% |
| 6 s | Begin as a Scholar: one subject group, with free notes and exercises. | 4.49 s | -5% |
| 11 s | Rise as a Knight: three subject groups, ten percent off. | 4.25 s | -5% |
| 16 s | Advance as a Noble: five subject groups, fifteen percent off. | 4.56 s | -5% |
| 21 s | Claim the throne as Royal: special price one-on-ones and a performance report. | 4.54 s | -5% |
| 26 s | For every level. Choose your path today. | 3.50 s | -5% |

The last two lines are shorter than in the brief. As first written they needed about 12.3 s between 21 s and 30 s, even at +10%.

### Rebuild

```
pip install numpy scipy pillow edge-tts
python3 src/package_combo_assets.py   # poster -> package-combo/public/ layers
python3 src/package_combo_vo.py       # edge-tts voice-over -> assets/vo/, timing -> vo.json
cd package-combo && npm install
npm run render                        # -> out/package-combo-30s.mp4
npm run still                         # -> out/final-frame.png
```
