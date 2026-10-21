"""Split the static poster into animatable layers.

Nothing here redraws text or faces: every layer is cut straight from the
original pixels. Where an object moves away from its spot, the hole is filled
with a "clean plate" rebuilt from the poster's own repeating blue grid.

Output: build/layers.npz plus debug PNGs in build/debug/.
"""
import os

import cv2
import numpy as np
from scipy import ndimage as ndi

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POSTER = os.path.join(ROOT, "assets", "poster.png")
BUILD = os.path.join(ROOT, "build")
DEBUG = os.path.join(BUILD, "debug")

# Measured grid period of the background (major lines), in px.
PX, PY = 54.71, 59.46

# Generous boxes around every piece of poster content (x0, y0, x1, y1).
# Anything outside them is treated as clean background for the grid fill.
CONTENT = [
    (320, 30, 720, 118),     # logo + brand name
    (0, 80, 372, 472),       # cubes, symbols, star
    (850, 20, 1080, 395),    # big atom
    (636, 306, 680, 350),    # star
    (562, 356, 672, 468),    # small atom
    (672, 286, 945, 428),    # ribbon
    (160, 400, 560, 508),    # tagline
    (866, 418, 1064, 552),   # right blurb
    (176, 446, 604, 664),    # Online
    (570, 366, 895, 705),    # centre figure
    (930, 570, 1030, 685),   # Ag
    (36, 565, 375, 900),     # left figure
    (466, 606, 920, 835),    # Class
    (196, 730, 710, 955),    # Tutoring
    (710, 730, 1035, 970),   # right figure
    (90, 870, 155, 935),     # star
    (450, 945, 494, 990),    # star
    (20, 930, 112, 1022),    # Br
    (100, 845, 445, 1140),   # left note
    (595, 915, 950, 1185),   # right note + cursor
    (620, 1160, 915, 1240),  # invest text
    (0, 1095, 295, 1350),    # car + ramp
    (840, 1105, 1080, 1335), # DNA
    (55, 1340, 1005, 1415),  # contact bar
    (85, 365, 170, 450),     # bokeh
]


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


def bilinear(a, x, y):
    x0, y0 = np.floor(x).astype(int), np.floor(y).astype(int)
    fx, fy = (x - x0)[:, None], (y - y0)[:, None]
    return (a[y0, x0] * (1 - fx) * (1 - fy) + a[y0, x0 + 1] * fx * (1 - fy)
            + a[y0 + 1, x0] * (1 - fx) * fy + a[y0 + 1, x0 + 1] * fx * fy)


def periodic_fill(img, target, valid, lf, reach=14):
    """Fill `target` pixels by copying the grid from whole periods away."""
    h, w = target.shape
    out = img.copy()
    ys, xs = np.nonzero(target)
    if len(ys) == 0:
        return out
    todo = np.ones(len(ys), bool)
    offs = [(i, j) for i in range(-reach, reach + 1) for j in range(-reach, reach + 1) if (i, j) != (0, 0)]
    offs.sort(key=lambda o: (o[0] * PX) ** 2 + (o[1] * PY) ** 2)
    for i, j in offs:
        if not todo.any():
            break
        cx = xs[todo] + i * PX
        cy = ys[todo] + j * PY
        rx, ry = np.round(cx).astype(int), np.round(cy).astype(int)
        inb = (rx >= 1) & (rx < w - 1) & (ry >= 1) & (ry < h - 1)
        ok = np.zeros(len(cx), bool)
        ok[inb] = valid[ry[inb], rx[inb]]
        if not ok.any():
            continue
        idx = np.nonzero(todo)[0][ok]
        src = bilinear(img, cx[ok], cy[ok])
        src_lf = bilinear(lf, cx[ok], cy[ok])
        dst_lf = lf[ys[idx], xs[idx]]
        out[ys[idx], xs[idx]] = src * dst_lf / np.maximum(src_lf, 1)
        todo[idx] = False
    return out


def largest_cc(mask, seed=None):
    n, lab = cv2.connectedComponents(mask.astype(np.uint8))
    if n <= 1:
        return mask
    if seed is not None:
        return lab == lab[seed[1], seed[0]]
    sizes = np.bincount(lab.ravel())
    sizes[0] = 0
    return lab == sizes.argmax()


def soft(mask, grow=0, feather=1.2):
    m = mask.astype(np.uint8)
    if grow > 0:
        m = cv2.dilate(m, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * grow + 1, 2 * grow + 1)))
    m = m.astype(np.float32)
    return np.clip(cv2.GaussianBlur(m, (0, 0), feather), 0, 1) if feather > 0 else m


def closed(mask, k):
    se = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k))
    return cv2.morphologyEx(mask.astype(np.uint8), cv2.MORPH_CLOSE, se) > 0


def main():
    os.makedirs(DEBUG, exist_ok=True)
    bgr = cv2.imread(POSTER, cv2.IMREAD_COLOR)
    img = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB).astype(np.float32)
    h, w = img.shape[:2]
    R, G, B = img[..., 0], img[..., 1], img[..., 2]

    content = box_mask((h, w), CONTENT)
    valid = ~cv2.dilate(content.astype(np.uint8), np.ones((5, 5), np.uint8)).astype(bool)
    lf = norm_blur(img, valid.astype(np.float32), 28)

    # Full background plate (used for the 9:16 extension and the bg mask).
    plate = periodic_fill(img, content, valid, lf)
    diff = np.abs(img - plate).max(2)
    content_soft = soft(closed(diff > 22, 9) | box_mask((h, w), [(55, 1340, 1005, 1415)]), grow=4, feather=4)
    bgmask = 1 - content_soft

    # Same comparison, but against a plate re-lit with the local haze, so the
    # soft glows around the floating cubes stay in the background.
    core = cv2.dilate((diff > 70).astype(np.uint8), np.ones((13, 13), np.uint8)) > 0
    lf_haze = norm_blur(img, (~core).astype(np.float32), 9)
    diff_haze = np.abs(img - plate * np.clip(lf_haze / np.maximum(lf, 1), 0.6, 1.8)).max(2)

    def obj_mask(box, thr=24, close_k=7, protect=None, haze=False):
        m = np.zeros((h, w), bool)
        x0, y0, x1, y1 = box
        m[y0:y1, x0:x1] = (diff_haze if haze else diff)[y0:y1, x0:x1] > thr
        m = ndi.binary_fill_holes(closed(m, close_k))
        m = cv2.morphologyEx(m.astype(np.uint8), cv2.MORPH_OPEN, np.ones((3, 3), np.uint8)) > 0
        if protect is not None:
            m &= ~protect
        return m

    # Ribbon: dark red band + its white lettering.
    rb = np.zeros((h, w), bool)
    rb[286:428, 672:945] = True
    ribbon_red = rb & (R > 110) & (G < 70) & (B < 70)
    ribbon = largest_cc(ndi.binary_fill_holes(closed(ribbon_red, 15)))
    ribbon_protect = cv2.dilate(ribbon.astype(np.uint8), np.ones((9, 9), np.uint8)) > 0

    text_protect = box_mask((h, w), [(620, 1160, 912, 1240)], pad=3)

    objs = {}
    cubes_left = obj_mask((0, 80, 200, 470), thr=30, haze=True, protect=box_mask((h, w), [(160, 400, 560, 508)]))
    # The toys are warm, green or white; the haze around them is grey-blue.
    toy = (R > G + 20) | (G > R + 40) | (img.min(2) > 200)
    tidy = lambda m: largest_cc(ndi.binary_fill_holes(closed(m, 9)))
    cubes_left = ndi.binary_fill_holes(closed(cubes_left & toy, 9))
    objs["cubes_left"] = cubes_left & ~box_mask((h, w), [(85, 365, 170, 450)])
    cube2 = obj_mask((140, 168, 368, 362), thr=30, haze=True)
    warm = (R > B + 40) & (R > 120)
    shared = cube2 & objs["cubes_left"]
    objs["cubes_left"] &= ~(shared & warm)
    objs["cube2"] = tidy(cube2 & ~(shared & ~warm) & toy)
    # the orange cube is far left; any warm pixel near cube 2 belongs to cube 2
    frag = objs["cubes_left"] & warm & box_mask((h, w), [(130, 160, 220, 380)])
    objs["cubes_left"] &= ~frag
    objs["cube2"] |= frag
    objs["divide"] = ndi.binary_fill_holes(closed(
        obj_mask((210, 90, 288, 168), thr=30, haze=True) & (B > 190) & (B - R > 80), 5))
    objs["plus"] = tidy(obj_mask((100, 300, 182, 388), thr=30, haze=True) & toy)
    objs["atom_big"] = obj_mask((850, 20, 1080, 395), protect=ribbon_protect)
    yy0, xx0 = np.mgrid[0:h, 0:w]
    disc = (xx0 - 618) ** 2 + (yy0 - 410) ** 2 < 52 ** 2
    objs["atom_small"] = obj_mask((562, 356, 672, 468), thr=34) & disc
    objs["ag"] = obj_mask((930, 570, 1030, 685))
    objs["br"] = obj_mask((20, 930, 112, 1022))
    objs["dna"] = obj_mask((850, 1110, 1080, 1335),
                           protect=text_protect | box_mask((h, w), [(595, 915, 950, 1185)], pad=3))
    bar = np.zeros((h, w), bool)
    bar[1340:1415, 55:1005] = (np.abs(img[1340:1415, 55:1005] - np.array([255, 255, 255])).max(2) < 60)
    objs["bar"] = ndi.binary_fill_holes(closed(largest_cc(bar), 9))

    # Car: GrabCut inside its box; ramp under the car is rebuilt by inpainting.
    gc = np.zeros((h, w), np.uint8)
    rect = (34, 1104, 212, 130)
    bgd, fgd = np.zeros((1, 65), np.float64), np.zeros((1, 65), np.float64)
    cv2.grabCut(bgr, gc, rect, bgd, fgd, 6, cv2.GC_INIT_WITH_RECT)
    car = (gc == cv2.GC_FGD) | (gc == cv2.GC_PR_FGD)
    car = largest_cc(ndi.binary_fill_holes(closed(car, 7)))
    objs["car"] = car

    # Per-object plates: grid fill above the ramp, inpaint on the ramp.
    plate_obj = img.copy()
    holes = np.zeros((h, w), bool)
    for name, m in objs.items():
        holes |= cv2.dilate(m.astype(np.uint8), np.ones((9, 9), np.uint8)) > 0
    holes &= ~ribbon_protect & ~text_protect
    yy, xx = np.mgrid[0:h, 0:w]
    ramp_line = 1180 + 0.135 * xx  # top edge of the ramp, under the car
    car_hole = cv2.dilate(car.astype(np.uint8), np.ones((9, 9), np.uint8)) > 0
    on_ramp = car_hole & (yy > ramp_line) & (xx < 300)
    grid_holes = holes & ~on_ramp
    valid2 = valid & ~holes
    plate_obj = periodic_fill(img, grid_holes, valid2, lf)
    # Keep the soft haze/glow that surrounds each object: re-light the filled
    # grid with the low-frequency colour of the pixels just around the hole.
    # Brightness only, so neighbouring colours (ramp, DNA) can't tint the fill.
    lf_local = norm_blur(img, (~holes).astype(np.float32), 9)
    relight = np.clip(lf_local.mean(2) / np.maximum(lf.mean(2), 1), 0.75, 1.6)[..., None]
    relit = grid_holes & ~car_hole & ~cv2.dilate(objs["dna"].astype(np.uint8), np.ones((15, 15), np.uint8)).astype(bool)
    plate_obj = np.where(relit[..., None], plate_obj * relight, plate_obj)
    u8 = np.clip(plate_obj, 0, 255).astype(np.uint8)
    inp = cv2.inpaint(cv2.cvtColor(u8, cv2.COLOR_RGB2BGR), on_ramp.astype(np.uint8), 7, cv2.INPAINT_TELEA)
    inp = cv2.cvtColor(inp, cv2.COLOR_BGR2RGB).astype(np.float32)
    plate_obj[on_ramp] = inp[on_ramp]
    sa = cv2.dilate(objs["atom_small"].astype(np.uint8), np.ones((9, 9), np.uint8))
    inp = cv2.inpaint(bgr, sa, 9, cv2.INPAINT_TELEA)
    inp = cv2.cvtColor(inp, cv2.COLOR_BGR2RGB).astype(np.float32)
    plate_obj[sa > 0] = inp[sa > 0]
    plate_obj = cv2.GaussianBlur(plate_obj, (0, 0), 0.6) * holes[..., None] + img * (~holes)[..., None]

    # ---- Title blocks (pop in place, never shrink below original). ----
    # Corners fitted to each block's edges (see README for how they were measured).
    def quad(pts, pad=2):
        m = np.zeros((h, w), np.uint8)
        c = np.array(pts, np.float32)
        c += (c - c.mean(0)) / np.linalg.norm(c - c.mean(0), axis=1, keepdims=True) * pad
        cv2.fillConvexPoly(m, np.round(c).astype(np.int32), 1)
        return m > 0

    near = lambda c, t: np.abs(img - np.array(c, np.float32)).max(2) < t
    online = quad([(195, 513), (579, 455), (600, 607), (166, 670)])
    klass = quad([(502, 617), (907, 693), (882, 847), (473, 776)])
    tutor = quad([(217, 741), (703, 796), (686, 950), (200, 895)])
    note_l = quad([(170, 861), (432, 940), (374, 1128), (112, 1047)], pad=1)
    note_r = quad([(618, 950), (927, 934), (938, 1156), (629, 1172)], pad=1)
    notes_white = note_l | note_r

    def palette_dist(cols):
        d = np.full((h, w), 1e9, np.float32)
        for c in cols:
            d = np.minimum(d, np.abs(img - np.array(c, np.float32)).max(2))
        return d

    def occluders(poly, member):
        occ = poly & ~member
        occ = cv2.morphologyEx(occ.astype(np.uint8), cv2.MORPH_OPEN, np.ones((3, 3), np.uint8)) > 0
        # keep only sizeable blobs (text antialiasing would otherwise sneak in)
        n, lab, st, _ = cv2.connectedComponentsWithStats(occ.astype(np.uint8))
        keep = np.zeros_like(occ)
        for i in range(1, n):
            if st[i, cv2.CC_STAT_AREA] > 120:
                keep |= lab == i
        return cv2.dilate(keep.astype(np.uint8), np.ones((5, 5), np.uint8)) > 0

    # Pixels that belong to a block: its fill, its lettering, or a blend of both.
    def blend_member(c1, c2, tol=30):
        a, b = np.array(c1, np.float32), np.array(c2, np.float32)
        d = b - a
        t = np.clip(((img - a) * d).sum(2) / (d * d).sum(), 0, 1)
        return np.abs(img - (a + t[..., None] * d)).max(2) < tol

    online_m = blend_member((255, 255, 255), (30, 10, 160), 40)
    class_m = blend_member((253, 233, 98), (150, 15, 20), 40)
    tutor_m = blend_member((155, 14, 18), (255, 255, 255), 40)
    occ_online = occluders(online, online_m)
    occ_class = occluders(klass, class_m)
    occ_tutor = occluders(tutor, tutor_m)

    # ---- Figures (GrabCut on the white-outlined stickers). ----
    def figure(rect):
        m = np.zeros((h, w), np.uint8)
        bgd, fgd = np.zeros((1, 65), np.float64), np.zeros((1, 65), np.float64)
        cv2.grabCut(bgr, m, rect, bgd, fgd, 5, cv2.GC_INIT_WITH_RECT)
        f = (m == cv2.GC_FGD) | (m == cv2.GC_PR_FGD)
        return largest_cc(ndi.binary_fill_holes(closed(f, 9)))

    solid = (content_soft > 0.5) & ~((B > R + 45) & (B > 100)) & ~(class_m & (G > 150))
    fig_c = figure((578, 372, 312, 330)) & ~klass & ~tutor & solid
    fig_l = figure((40, 568, 330, 330)) & ~tutor & ~notes_white & solid & ~(online & online_m)
    fig_r = figure((712, 732, 322, 236)) & ~(klass & class_m) & ~notes_white & solid
    fig_c, fig_l, fig_r = [
        largest_cc(ndi.binary_fill_holes(cv2.morphologyEx(f.astype(np.uint8), cv2.MORPH_OPEN, np.ones((5, 5), np.uint8)) > 0))
        for f in (fig_c, fig_l, fig_r)]

    # Front occluders for each figure: blocks / notes / pins drawn in front.
    pin_g = (G > 120) & (G > R + 50) & (G > B + 50)
    pin_l = largest_cc(closed(pin_g & box_mask((h, w), [(280, 850, 370, 940)]), 7))
    pin_r = largest_cc(closed(pin_g & box_mask((h, w), [(755, 870, 840, 980)]), 7))

    def needle(pin_mask, box):
        x0, y0, x1, y1 = box
        z = np.zeros((h, w), bool)
        sub = img[y0:y1, x0:x1]
        grey = (np.abs(sub[..., 0] - sub[..., 1]) < 25) & (np.abs(sub[..., 1] - sub[..., 2]) < 30) & \
            (sub.mean(2) > 70) & (sub.mean(2) < 215)
        z[y0:y1, x0:x1] = grey
        z = cv2.dilate(z.astype(np.uint8), np.ones((2, 2), np.uint8)) > 0
        grow = cv2.dilate(pin_mask.astype(np.uint8), np.ones((5, 5), np.uint8)) > 0
        # walk the grey pixels that touch the green head
        return ndi.binary_propagation(grow & z, mask=z) | pin_mask

    pin_l = needle(pin_l, (270, 880, 345, 945))
    pin_r = needle(pin_r, (760, 920, 800, 985))
    pins = pin_l | pin_r

    dil = lambda m, k=3: cv2.dilate(m.astype(np.uint8), np.ones((k, k), np.uint8)) > 0
    occ_online |= dil((fig_c | fig_l | klass) & online)
    occ_class |= dil((tutor | fig_r) & klass)
    occ_tutor = occluders(tutor, tutor_m) & ~notes_white | dil((notes_white | pins) & tutor)

    front_c = klass | tutor
    front_l = tutor | note_l | pin_l
    front_r = note_r | pin_r

    np.savez_compressed(
        os.path.join(BUILD, "layers.npz"),
        img=img.astype(np.uint8), plate=np.clip(plate, 0, 255).astype(np.uint8),
        plate_obj=np.clip(plate_obj, 0, 255).astype(np.uint8),
        bgmask=bgmask.astype(np.float16), lf=lf.astype(np.float16),
        ribbon=ribbon,
        online=online, klass=klass, tutor=tutor,
        occ_online=occ_online, occ_class=occ_class, occ_tutor=occ_tutor,
        fig_c=fig_c, fig_l=fig_l, fig_r=fig_r,
        front_c=front_c, front_l=front_l, front_r=front_r,
        pin_l=pin_l, pin_r=pin_r,
        **{"obj_" + k: v for k, v in objs.items()},
    )

    # Debug views.
    def save(name, arr):
        cv2.imwrite(os.path.join(DEBUG, name), cv2.cvtColor(np.clip(arr, 0, 255).astype(np.uint8), cv2.COLOR_RGB2BGR))

    save("plate_full.png", plate)
    save("plate_obj.png", plate_obj)
    over = img * 0.35
    palette = [(255, 80, 80), (80, 255, 80), (80, 160, 255), (255, 255, 80), (255, 80, 255), (80, 255, 255)]
    for i, (k, m) in enumerate(list(objs.items()) + [("pin_l", pin_l), ("pin_r", pin_r), ("ribbon", ribbon)]):
        over[m] = over[m] * 0.3 + np.array(palette[i % 6]) * 0.7
    save("objects.png", over)
    over = img * 0.35
    for i, m in enumerate([online, klass, tutor]):
        over[m] = img[m] * 0.6 + np.array(palette[i]) * 0.4
    for m in [occ_online, occ_class, occ_tutor]:
        over[m] = np.array((255, 0, 255))
    save("blocks.png", over)
    over = img * 0.3
    for i, m in enumerate([fig_c, fig_l, fig_r]):
        over[m] = img[m]
    save("figures.png", over)
    save("bgmask.png", np.repeat(bgmask[..., None] * 255, 3, 2))


if __name__ == "__main__":
    main()
