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
