"""Cut the Package Combo poster into layers for the Remotion video.

Writes into package-combo/public/:
  plate.png            background with logo, header, title, table and characters removed
  char_<name>.png      full-frame RGBA cut-outs (scholar, knight, noble, king)
  logo.png, header.png alpha crops of the top lock-up
  card_*.png, bar_*.png crops of the white card / contact bar contents (on white)
  layout.json          measured geometry used by the React components
"""
import json
import os
import shutil

import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from scipy import ndimage as ndi

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POSTER = os.path.join(ROOT, "assets", "package-combo", "poster.png")
PUB = os.path.join(ROOT, "package-combo", "public")
os.makedirs(PUB, exist_ok=True)

src = np.asarray(Image.open(POSTER).convert("RGB")).astype(np.float32)
H, W, _ = src.shape
YY, XX = np.mgrid[0:H, 0:W]

# ------------------------------------------------------------------ geometry
COLS = [(57, 259), (262, 636), (639, 1023)]
ROWS = [(284, 380), (383, 501), (504, 626), (629, 904)]
CARD = (128, 1171, 953, 1308, 20)  # x0, y0, x1, y1, radius
BAR_Y = (1354, 1401)
PAINT_TOP = 845

# grid (measured from the clean background)
GX0, GPX = 20.0, 27.345
GY0, GPY = 6.4, 29.77


def rounded_mask(x0, y0, x1, y1, r, grow=0):
    m = Image.new("L", (W, H), 0)
    ImageDraw.Draw(m).rounded_rectangle((x0 - grow, y0 - grow, x1 + grow, y1 + grow), r + grow, fill=255)
    return np.asarray(m) > 127


def rows_runs(v):
    out, s = [], None
    for i, x in enumerate(v):
        if x and s is None:
            s = i
        if not x and s is not None:
            out.append((s, i))
            s = None
    if s is not None:
        out.append((s, len(v)))
    return out


white = src.min(2) > 245
BAR = (65, BAR_Y[0], 994, BAR_Y[1], (BAR_Y[1] - BAR_Y[0]) / 2)
card_mask = rounded_mask(*CARD[:4], CARD[4], grow=2)
bar_mask = rounded_mask(*BAR[:4], int(BAR[4]), grow=2)

# ------------------------------------------------------------------ painting: fill card + bar
paint = src.copy()


def mirror_fill(img, mask, y0, y1):
    """Fill rows y0..y1 by blending reflections from above and below (keeps brush texture)."""
    h = y1 - y0
    out = img.copy()
    for k in range(h):
        y = y0 + k
        above = img[max(0, y0 - 1 - k)]
        below = img[min(H - 1, y1 + (h - 1 - k))]
        w = (k + 0.5) / h
        w = w * w * (3 - 2 * w)
        row = above * (1 - w) + below * w
        m = mask[y]
        out[y, m] = row[m]
    return out


paint = mirror_fill(paint, bar_mask, BAR[1] - 2, BAR[3] + 2)
paint = mirror_fill(paint, card_mask, CARD[1] - 2, CARD[3] + 2)
soft = np.stack([ndi.gaussian_filter(paint[..., c], 2.0) for c in range(3)], -1)
fillm = (card_mask | bar_mask)[..., None]
paint = np.where(fillm, soft, paint)

# ------------------------------------------------------------------ smooth background model
lum = src.mean(2)
loc_std = np.sqrt(np.maximum(ndi.uniform_filter(lum ** 2, 7) - ndi.uniform_filter(lum, 7) ** 2, 0))

excl = np.zeros((H, W), bool)
excl[30:118, 318:406] = True                          # logo
excl[55:95, 412:718] = True                           # header text
excl[160:272, 250:835] = True                         # title + shadow
excl[ROWS[0][0] - 3:ROWS[3][1] + 4, COLS[0][0] - 3:COLS[2][1] + 3] = True  # table

# sky key inside the painted area
blueish = (src[..., 2] > src[..., 0] + 45) & (src[..., 2] > src[..., 1] + 25)
cand = blueish & (loc_std < 6.0) & (YY >= PAINT_TOP) & ~excl


def norm_conv(img, mask, sigmas=(18, 60, 220)):
    out = np.zeros_like(img)
    have = np.zeros(mask.shape, bool)
    for s in sigmas:
        den = ndi.gaussian_filter(mask.astype(np.float32), s)
        num = np.stack([ndi.gaussian_filter(img[..., c] * mask, s) for c in range(3)], -1)
        est = num / np.maximum(den, 1e-6)[..., None]
        take = (~have) & (den > 0.08)
        out[take] = est[take]
        have |= take
    out[~have] = est[~have]
    return out


# grid line pixels shouldn't bias the smooth fit
phx = ((XX - GX0) % GPX)
phy = ((YY - GY0) % GPY)
on_grid = (np.minimum(phx, GPX - phx) < 2.0) | (np.minimum(phy, GPY - phy) < 2.0)

clean_top = (~excl) & (YY < PAINT_TOP) & (~on_grid)
sky_model_src = clean_top | (cand & ~on_grid)
smooth = norm_conv(src, sky_model_src)

# sky key: smooth blue areas (texture measured after a median that erases the grid and
# table rules) flood-filled from the open sky, then edges refined against a local sky model
med = np.stack([ndi.median_filter(src[..., c], 7) for c in range(3)], -1)
ml = med.mean(2)
tex = np.sqrt(np.maximum(ndi.uniform_filter(ml ** 2, 9) - ndi.uniform_filter(ml, 9) ** 2, 0))
blue_m = med[..., 2] - np.maximum(med[..., 0], med[..., 1] * 0.6)
skyish = (YY >= PAINT_TOP) & (tex < 6.5) & (blue_m > 30)
seeds = np.zeros((H, W), bool)
seeds[PAINT_TOP:PAINT_TOP + 6] = True
seeds[908:916] = True
lab, _ = ndi.label(skyish)
keep = set(np.unique(lab[seeds & skyish])) - {0}
sky = np.isin(lab, list(keep))
sky = ndi.binary_closing(sky, structure=np.ones((5, 5)), iterations=1) | sky
conf = ndi.binary_erosion(sky, iterations=4)
sky_col = norm_conv(src, conf & ~on_grid, sigmas=(10, 30, 120))
cdist = np.sqrt(((src - sky_col) ** 2).sum(2))
band = ndi.binary_dilation(sky, iterations=8) & ~ndi.binary_erosion(sky, iterations=8)
sky = np.where(band, cdist < 26, sky)
sky = ndi.binary_opening(sky, iterations=1)
sky |= YY < PAINT_TOP
fg = (~sky) & (YY >= PAINT_TOP)
# table rules and cell fill above the horizon belong to the table, not the art
raw_blue = (src[..., 2] > src[..., 0] + 45) & (src[..., 2] > src[..., 1] + 25)
fg &= ~((YY < 910) & raw_blue)
fg = ndi.binary_opening(fg, iterations=1)
lab, n = ndi.label(fg)
sizes = ndi.sum(fg, lab, range(1, n + 1))
fg = np.isin(lab, [i + 1 for i, s in enumerate(sizes) if s > 400])
# keep the plate fill away from the soft edge
sky_for_plate = sky & ~ndi.binary_dilation(fg, iterations=2)

# grid template from residuals of clean background
resid = src - smooth
clean_any = ((~excl) & (YY < PAINT_TOP)) | (sky_for_plate & (YY >= PAINT_TOP))
bx = np.round(phx * 2).astype(int)
by = np.round(phy * 2).astype(int)
tx = np.zeros((bx.max() + 1, 3))
ty = np.zeros((by.max() + 1, 3))
for c in range(3):
    r = resid[..., c]
    tx[:, c] = ndi.median(r, bx * clean_any + (~clean_any) * (bx.max() + 5), range(bx.max() + 1))
    ty[:, c] = ndi.median(r, by * clean_any + (~clean_any) * (by.max() + 5), range(by.max() + 1))
tx -= np.median(tx, 0)
ty -= np.median(ty, 0)
grid = tx[bx] + ty[by]
synth = smooth + grid


def row_lerp(img, x0, y0, x1, y1, m=6):
    """Fill a rectangle by blending, per row, the clean colour just left and right of it."""
    left = img[y0:y1, max(0, x0 - m):x0].mean(1)
    right = img[y0:y1, x1:min(W, x1 + m)].mean(1)
    left = ndi.gaussian_filter1d(left, 6, axis=0)
    right = ndi.gaussian_filter1d(right, 6, axis=0)
    t = np.linspace(0, 1, x1 - x0)[None, :, None]
    t = t * t * (3 - 2 * t)
    return left[:, None] * (1 - t) + right[:, None] * t


base = smooth.copy()
for (x0, y0, x1, y1) in [(318, 30, 406, 118), (412, 55, 718, 95), (250, 160, 835, 272),
                         (COLS[0][0] - 3, ROWS[0][0] - 3, COLS[2][1] + 3, PAINT_TOP)]:
    base[y0:y1, x0:x1] = row_lerp(smooth, x0, y0, x1, y1)
synth = base + grid

# sky behind the art: interpolate each row between the visible sky on either side,
# then soften, so the hole left by the characters reads as open sky
open_sky = sky_for_plate & ~excl & (YY >= PAINT_TOP) & ~on_grid
sky_rows = np.zeros((H, W, 3), np.float32)
xs = np.arange(W)
last = None
for y in range(PAINT_TOP, H):
    m = open_sky[y]
    if m.sum() > 20:
        kx = xs[m]
        for c in range(3):
            sky_rows[y, :, c] = np.interp(xs, kx, src[y, m, c])
        last = sky_rows[y]
    elif last is not None:
        sky_rows[y] = last
for c in range(3):
    sky_rows[PAINT_TOP:, :, c] = ndi.gaussian_filter(sky_rows[PAINT_TOP:, :, c], (10, 14))
sky_fill = sky_rows + grid
lowsky = YY >= PAINT_TOP
synth = np.where(lowsky[..., None], sky_fill, synth)

# ------------------------------------------------------------------ plate
plate = src.copy()
plate[excl] = synth[excl]
plate[fg] = synth[fg]
# below the horizon nothing of the real sky shows: sink it into a deep navy floor
sky_vis = sky_for_plate & (YY >= PAINT_TOP) & ~(card_mask | bar_mask)
lowest = int(np.nonzero(sky_vis.any(1))[0].max())
fade = np.clip((YY - lowest) / 200.0, 0, 1)
fade = (fade * fade * (3 - 2 * fade))[..., None]
navy = np.array([10, 22, 62], np.float32)
plate = np.where(fg[..., None], plate * (1 - 0.9 * fade) + navy * 0.9 * fade, plate)
plate = np.where((card_mask | bar_mask)[..., None], synth * (1 - 0.9 * fade) + navy * 0.9 * fade, plate)
Image.fromarray(np.clip(plate, 0, 255).astype(np.uint8)).save(os.path.join(PUB, "plate.png"))
print("lowest visible sky row", lowest)

# softened plate for the first 21 s: same sky, no lumps where the characters were cut out
w = np.clip((YY - (PAINT_TOP - 30)) / 60.0, 0, 1)[..., None]
base_lo = plate - grid
soft_lo = np.stack([ndi.gaussian_filter(base_lo[..., c], 28) for c in range(3)], -1) + grid
early = plate * (1 - w) + soft_lo * w
Image.fromarray(np.clip(early, 0, 255).astype(np.uint8)).save(os.path.join(PUB, "plate_early.png"))

# ------------------------------------------------------------------ characters
POLY = {
    "knight": [(0, 900), (125, 900), (150, 1020), (212, 1036), (218, 1100), (175, 1140), (145, 1200),
               (138, 1440), (0, 1440)],
    "king": [(196, 850), (522, 850), (532, 1000), (560, 1058), (576, 1120), (590, 1440), (138, 1440),
             (145, 1200), (175, 1140), (218, 1100), (212, 1036), (196, 1000)],
    "noble": [(522, 850), (842, 850), (836, 1000), (826, 1050), (866, 1090), (876, 1170), (862, 1440),
              (590, 1440), (576, 1120), (560, 1058), (532, 1000)],
    "scholar": [(842, 850), (1080, 850), (1080, 1440), (862, 1440), (876, 1170), (866, 1090), (826, 1050),
                (836, 1000)],
}
DEPTH = {"king": 0, "knight": 1, "noble": 1, "scholar": 2}


def poly_mask(pts):
    m = Image.new("L", (W, H), 0)
    ImageDraw.Draw(m).polygon(pts, fill=255)
    return np.asarray(m) > 127


polys = {k: poly_mask(v) for k, v in POLY.items()}
fg_alpha = ndi.gaussian_filter(fg.astype(np.float32), 0.9)
fg_alpha = np.clip((fg_alpha - 0.15) / 0.7, 0, 1)
boxes = {}
for name, pm in polys.items():
    front = np.zeros((H, W), bool)
    for other, om in polys.items():
        if DEPTH[other] > DEPTH[name]:
            front |= om
    region = pm | (ndi.binary_dilation(pm, iterations=36) & front)
    region_a = ndi.gaussian_filter(region.astype(np.float32), 0.7)
    a = np.clip(fg_alpha * region_a * 1.02, 0, 1)
    rgba = np.dstack([np.clip(paint, 0, 255), a * 255]).astype(np.uint8)
    Image.fromarray(rgba, "RGBA").save(os.path.join(PUB, f"char_{name}.png"))
    ys, xs = np.nonzero(a > 0.05)
    boxes[name] = [int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1]

# ------------------------------------------------------------------ logo + header (alpha from background)
LOGO_C, LOGO_R = (362, 74), 38.5
d = np.hypot(XX - LOGO_C[0], YY - LOGO_C[1])
la = np.clip(LOGO_R + 0.5 - d, 0, 1)
x0, y0 = LOGO_C[0] - 41, LOGO_C[1] - 41
logo = np.dstack([src, la * 255])[y0:y0 + 82, x0:x0 + 82]
Image.fromarray(logo.astype(np.uint8), "RGBA").save(os.path.join(PUB, "logo.png"))

hx0, hy0, hx1, hy1 = 412, 55, 718, 95
crop = src[hy0:hy1, hx0:hx1]
bg = synth[hy0:hy1, hx0:hx1]
alpha = np.clip(((crop - bg) / np.maximum(255 - bg, 1)).mean(2), 0, 1)
alpha[alpha < 0.04] = 0
hdr = np.dstack([np.full_like(alpha, 255)] * 3 + [alpha * 255])
Image.fromarray(hdr.astype(np.uint8), "RGBA").save(os.path.join(PUB, "header.png"))

# ------------------------------------------------------------------ card + bar contents (sit on white)
srci = Image.open(POSTER).convert("RGB")
pieces = {
    "card_title": (370, 1175, 686, 1210),
    "card_b1": (156, 1220, 434, 1255),
    "card_b2": (156, 1261, 470, 1296),
    "card_b3": (522, 1220, 890, 1255),
    "card_b4": (522, 1261, 918, 1296),
}
nonwhite = ~white
segs = [(78 + s, 78 + e) for s, e in rows_runs(nonwhite[BAR[1] + 10:BAR[3] - 10, 78:982].any(0))]
groups, cur = [], None
for s, e in segs:
    if cur and s - cur[1] <= 9:
        cur[1] = e
    else:
        if cur:
            groups.append(cur)
        cur = [s, e]
groups.append(cur)
# label | email | phone | instagram | tiktok
names = ["bar_label", "bar_email", "bar_phone", "bar_insta", "bar_tiktok"]
assert len(groups) == 5, groups
for n, (s, e) in zip(names, groups):
    pieces[n] = (s - 3, BAR[1] + 4, e + 3, BAR[3] - 4)
for n, box in pieces.items():
    srci.crop(box).save(os.path.join(PUB, f"{n}.png"))

layout = {
    "cols": COLS, "rows": ROWS, "card": CARD, "bar": [int(v) if i < 4 else float(v) for i, v in enumerate(BAR)],
    "pieces": {k: list(map(int, v)) for k, v in pieces.items()},
    "chars": boxes, "logo": [x0, y0, 82, 82], "header": [hx0, hy0, hx1 - hx0, hy1 - hy0],
}
with open(os.path.join(PUB, "layout.json"), "w") as f:
    json.dump(layout, f, indent=1)

shutil.copyfile(os.path.join(ROOT, "out", "royal_fanfare_30s.mp3"), os.path.join(PUB, "royal_fanfare_30s.mp3"))
print(json.dumps(layout))
