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

---

# Subjects Offered – 30 s animated poster (Remotion)

`out/subjects-offered-30s.mp4` is a 30 s, 1080×1440, 30 fps (900 frames) H.264 video of the "Subjects Offered" poster (`assets/subjects-offered/poster.png`). `out/final-frame.png` is frame 899, for comparison with the poster.

The tutors, logo and background are cut from the poster's own pixels. All text, the table, the card and the contact bar are rebuilt as vector graphics so they can animate. The font is Outfit (600/700), the closest free match to the poster's lettering, with sizes and spacing fitted to the poster's text boxes.

| Time | What happens |
|---|---|
| 0–3 s | Grid background fades in under a diagonal light sweep; logo and "Studyolution Academy" fade and scale in. |
| 3–8 s | Tutors rise on a soft spring: Sir Isaac, then Cikgu Ashraf and Cikgu Natasha, then Teacher Sharmila and Cikgu Claudia. Each name label fades in above. |
| 8–10 s | "Subjects Offered" punches in with a bounce and a glow flare. |
| 10–15 s | Table border draws itself; group 1 subjects slide in one by one; middle cell fades in; prices count up (RM 50, RM 130). |
| 15–20 s | Group 2, same style (RM 90, RM 239). |
| 20–25 s | Group 3 (RM 239), then a highlight pulse across the three price cells. |
| 25–28 s | "Available for all levels:" card slides up, bullets appear one by one. |
| 28–30 s | Contact bar slides up with its icons; final frame holds. The background keeps drifting slowly throughout. |

## Rebuild

```
pip install opencv-python-headless scipy numpy rembg pillow
python3 video/scripts/prepare_assets.py    # cut-outs, logo, clean background -> video/public/
cd video && npm install
node scripts/stills.mjs 90 270 450 600 899 # preview stills -> build/so/stills/
npm run render                             # -> out/subjects-offered-30s.mp4 and out/final-frame.png
python3 scripts/compare.py ../build/so/stills/frame-899.png  # side-by-side and diff against the poster
```

If `assets/tutors/<name>.png` (isaac, ashraf, natasha, sharmila, claudia) exist, they are used instead of the poster cut-outs. If `assets/music.mp3` exists, it is added with a 1 s fade-out at the end.
