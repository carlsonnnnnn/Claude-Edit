"""Cut the animatable layers for the "Subjects Offered" video out of the poster.

    pip install opencv-python-headless scipy numpy rembg pillow
    python3 video/scripts/prepare_assets.py

Writes into video/public/:
  bg.png            the poster background with all content removed (grid rebuilt
                    from whole grid periods away, so it lines up with the poster)
  logo.png          the round academy logo
  tutor_<name>.png  one cut-out per tutor, all the same size, to be placed at
                    TUTOR_BOX (x, y) on the 1080x1440 canvas. The "Subjects
                    Offered" title is painted out of the suits underneath it.

Uses ./assets/tutors/<name>.png instead of cutting, and copies ./assets/music.mp3, if present.
"""
import json
import os
import shutil

import cv2
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ASSETS = os.path.join(ROOT, "assets", "subjects-offered")
POSTER = os.path.join(ASSETS, "poster.png")
PUBLIC = os.path.join(ROOT, "video", "public")
BUILD = os.path.join(ROOT, "build", "so")

# Background grid period (major lines), measured on the poster.
PX, PY = 54.71, 59.46

# Everything that is not background, as (x0, y0, x1, y1) boxes.
CONTENT = [
    (318, 30, 722, 114),     # logo + brand name
    (188, 100, 925, 405),    # tutors, name labels, title
    (78, 386, 1002, 1224),   # table and its glossy rim
    (120, 1218, 960, 1340),  # levels card
    (58, 1348, 1000, 1406),  # contact bar
]

# Tutor strip (x0, y0, x1, y1). Name labels sit above y=190 and are drawn live.
TUTOR_BOX = (180, 140, 940, 404)
LOGO_C, LOGO_R = (361, 73), 38

# Boundaries between neighbouring tutors, as polylines in strip coordinates
# (top to bottom). Order left to right: Sharmila | Ashraf | Isaac | Natasha | Claudia.
SPLITS = [
    [(178, 0), (176, 100), (160, 135), (153, 170), (150, 264)],
    [(292, 0), (293, 95), (300, 110), (290, 130), (280, 160), (276, 264)],
    [(395, 0), (392, 100), (440, 128), (450, 160), (458, 264)],
    [(548, 0), (545, 100), (570, 140), (578, 180), (580, 264)],
]
NAMES = ["sharmila", "ashraf", "isaac", "natasha", "claudia"]
# Strip row below which each pair's shoulders overlap (pair = left index).
SHOULDER = [135, 115, 115, 140]
# Poster row where the table rim starts covering the bodies.
BODY_CUT = 390
# Draw order back to front; back layers get a hidden extension under the front ones
# so no notch opens up while they rise.
DEPTH = {"sharmila": 0, "claudia": 0, "ashraf": 1, "natasha": 1, "isaac": 2}


def box_mask(shape, boxes, pad=0):
    m = np.zeros(shape, bool)
    for x0, y0, x1, y1 in boxes:
        m[max(0, y0 - pad):y1 + pad, max(0, x0 - pad):x1 + pad] = True
    return m


def norm_blur(img, w, sigma):
    """Low-frequency colour of the valid pixels, extrapolated into big holes."""
    out = None
    for s in (sigma, sigma * 3, sigma * 8):
        num = cv2.GaussianBlur(img * w[..., None], (0, 0), s)
        den = cv2.GaussianBlur(w, (0, 0), s)[..., None]
        est = num / np.maximum(den, 1e-6)
        if out is None:
            out, conf = est, den
        else:
            a = np.clip(conf / 0.08, 0, 1)
            out = out * a + est * (1 - a)
            conf = np.maximum(conf, den)
    return out


def grid_tile(ratio, valid, step=0.5):
    """Median grid modulation for each sub-pixel phase of one grid period."""
    h, w = valid.shape
    ys, xs = np.nonzero(valid)
    nx, ny = int(np.ceil(PX / step)), int(np.ceil(PY / step))
    bx = ((xs % PX) / step).astype(int)
    by = ((ys % PY) / step).astype(int)
    key = by * nx + bx
    order = np.argsort(key, kind="stable")
    key_s = key[order]
    vals = ratio[ys[order], xs[order]]
    tile = np.ones((ny * nx, 3), np.float32)
    bounds = np.searchsorted(key_s, np.arange(ny * nx + 1))
    for k in range(ny * nx):
        a, b = bounds[k], bounds[k + 1]
        if b > a:
            tile[k] = np.median(vals[a:b], 0)
    return tile.reshape(ny, nx, 3), nx, step


def background(rgb):
    """Smooth lighting x one averaged grid period. Visible background is kept
    as is; the holes left by the content get lighting extrapolated from
    around them and the same grid, so lines line up with the poster's."""
    img = rgb.astype(np.float32)
    h, w = img.shape[:2]
    content = box_mask((h, w), CONTENT)
    valid = ~cv2.dilate(content.astype(np.uint8), np.ones((9, 9), np.uint8)).astype(bool)
    # Lighting: blur away the grid lines (they are thin) before estimating.
    base = cv2.medianBlur(rgb.astype(np.uint8), 7).astype(np.float32)
    lf = norm_blur(base, valid.astype(np.float32), 40)
    lf_local = norm_blur(base, valid.astype(np.float32), 10)
    ratio = img / np.maximum(lf_local, 1)
    tile, nx, step = grid_tile(ratio, valid & (np.abs(ratio - 1).max(2) < 0.6))
    yy, xx = np.mgrid[0:h, 0:w]
    tb = tile[((yy % PY) / step).astype(int), ((xx % PX) / step).astype(int)]
    synth = lf * tb
    soft = cv2.GaussianBlur(content.astype(np.float32), (0, 0), 3)[..., None]
    plate = synth * soft + img * (1 - soft)
    return np.clip(plate, 0, 255).astype(np.uint8)


def logo(rgb):
    (cx, cy), r = LOGO_C, LOGO_R
    pad = 2
    x0, y0 = cx - r - pad, cy - r - pad
    patch = rgb[y0:cy + r + pad + 1, x0:cx + r + pad + 1]
    yy, xx = np.mgrid[0:patch.shape[0], 0:patch.shape[1]]
    d = np.hypot(xx - (r + pad), yy - (r + pad))
    a = np.clip(r + 0.5 - d, 0, 1)
    return np.dstack([patch, (a * 255).astype(np.uint8)])


def title_mask(rgb):
    """White 'Subjects Offered' letters plus their navy drop shadow."""
    h, w = rgb.shape[:2]
    m = np.zeros((h, w), np.uint8)
    region = rgb[325:404, 300:760].astype(int)
    white = (region.min(2) > 150).astype(np.uint8)
    m[325:404, 300:760] = white
    m = cv2.dilate(m, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7)))
    shadow = np.zeros_like(m)
    for dx in range(0, 13, 2):
        for dy in range(0, 15, 2):
            shadow = np.maximum(shadow, np.roll(np.roll(m, dy, 0), dx, 1))
    return cv2.dilate(np.maximum(m, shadow), np.ones((3, 3), np.uint8))


def side_of(poly, shape):
    """Boolean mask of pixels left of a top-to-bottom polyline."""
    h, w = shape
    pts = np.array(poly + [(0, h), (0, 0)], np.int32)
    m = np.zeros(shape, np.uint8)
    cv2.fillPoly(m, [pts], 1)
    return m.astype(bool)


def tutors(rgb):
    from PIL import Image
    from rembg import new_session, remove

    x0, y0, x1, y1 = TUTOR_BOX
    cut = BODY_CUT - y0
    # Paint the title (and the strip of table rim under the bodies) out of the
    # poster, working only above the table so its blue never bleeds in.
    tm = title_mask(rgb)[:y1]
    tm[BODY_CUT:y1, x0:x1] = 1
    top = rgb[:y1, :, ::-1].copy()
    clean = cv2.inpaint(top, tm, 6, cv2.INPAINT_TELEA)
    clean = cv2.inpaint(clean, tm, 3, cv2.INPAINT_NS)[..., ::-1]
    strip = rgb[y0:y1, x0:x1]
    strip_clean = clean[y0:y1, x0:x1]
    # Segment on the original strip (the model sees the true silhouettes).
    seg = remove(Image.fromarray(strip), session=new_session("birefnet-portrait"))
    alpha = np.asarray(seg)[..., 3].astype(np.float32) / 255
    # Drop stray specks (bits of label text).
    hard = (alpha > 0.5).astype(np.uint8)
    n, lab, stats, _ = cv2.connectedComponentsWithStats(hard)
    keep = np.zeros_like(hard)
    for i in range(1, n):
        if stats[i, cv2.CC_STAT_AREA] > 2000:
            keep[lab == i] = 1
    alpha *= cv2.dilate(keep, np.ones((5, 5), np.uint8))
    # Below the cut the poster shows the table rim: continue the bodies down.
    alpha[cut:] = alpha[cut - 1]

    shape = alpha.shape
    lefts = [side_of(p, shape) for p in SPLITS]
    regions = []
    for i in range(5):
        r = np.ones(shape, bool)
        if i > 0:
            r &= ~lefts[i - 1]
        if i < 4:
            r &= lefts[i]
        regions.append(r)

    os.makedirs(BUILD, exist_ok=True)
    out = {}
    for i, name in enumerate(NAMES):
        own = regions[i]
        a = alpha * cv2.GaussianBlur(own.astype(np.float32), (0, 0), 0.8)
        col = strip_clean.copy()
        # Back layers: extend under the front neighbours (below the shoulders) by
        # copying the nearest own body pixel, so rising never opens a notch.
        ext = np.zeros(shape, bool)
        for j, other in enumerate(NAMES):
            if abs(j - i) == 1 and DEPTH[other] > DEPTH[name]:
                r = regions[j].copy()
                r[:SHOULDER[min(i, j)]] = False
                ext |= r
        body = own & (alpha > 0.6)
        if ext.any():
            near = cv2.dilate(body.astype(np.uint8), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (61, 61))).astype(bool)
            ext &= near & (alpha > 0.5)
            _, idx = cv2.distanceTransformWithLabels((~body).astype(np.uint8), cv2.DIST_L2, 5,
                                                     labelType=cv2.DIST_LABEL_PIXEL)
            ys, xs = np.nonzero(body)
            lut = np.zeros((idx.max() + 1, 2), int)
            lut[idx[ys, xs]] = np.stack([ys, xs], 1)
            ey, ex = np.nonzero(ext)
            src = lut[idx[ey, ex]]
            fill = col.copy()
            fill[ey, ex] = strip_clean[src[:, 0], src[:, 1]]
            fill = cv2.GaussianBlur(fill, (0, 0), 3)
            col[ey, ex] = fill[ey, ex]
            a = np.maximum(a, alpha * ext)
        rgba = np.dstack([col, np.clip(a * 255, 0, 255).astype(np.uint8)])
        out[name] = rgba
        dbg = (col * a[..., None] + np.array([255, 0, 255]) * (1 - a[..., None])).astype(np.uint8)
        cv2.imwrite(os.path.join(BUILD, f"tutor_{name}.png"), dbg[..., ::-1])
    return out


def save_rgba(path, rgba):
    bgra = rgba[..., [2, 1, 0, 3]] if rgba.shape[2] == 4 else rgba[..., ::-1]
    cv2.imwrite(path, bgra)


def main():
    os.makedirs(PUBLIC, exist_ok=True)
    rgb = cv2.imread(POSTER, cv2.IMREAD_COLOR)[..., ::-1].copy()
    save_rgba(os.path.join(PUBLIC, "bg.png"), background(rgb))
    save_rgba(os.path.join(PUBLIC, "logo.png"), logo(rgb))
    supplied = os.path.join(ROOT, "assets", "tutors")
    if os.path.isdir(supplied) and all(os.path.exists(os.path.join(supplied, f"{n}.png")) for n in NAMES):
        for n in NAMES:
            shutil.copy(os.path.join(supplied, f"{n}.png"), os.path.join(PUBLIC, f"tutor_{n}.png"))
    else:
        for name, rgba in tutors(rgb).items():
            save_rgba(os.path.join(PUBLIC, f"tutor_{name}.png"), rgba)
    shutil.copy(POSTER, os.path.join(PUBLIC, "poster.png"))
    music = os.path.join(ROOT, "assets", "music.mp3")
    if os.path.exists(music):
        shutil.copy(music, os.path.join(PUBLIC, "music.mp3"))
    with open(os.path.join(PUBLIC, "layout.json"), "w") as f:
        json.dump({"tutorBox": TUTOR_BOX, "logo": {"cx": LOGO_C[0], "cy": LOGO_C[1], "r": LOGO_R},
                   "music": os.path.exists(music)}, f, indent=2)
    print("wrote", sorted(os.listdir(PUBLIC)))


if __name__ == "__main__":
    main()
