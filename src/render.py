"""Render the 8 s, 1080x1920 (9:16) Studyolution Academy promo.

Run src/layers.py first. Frame 0 and the final hold are the poster itself,
pixel for pixel; in between, every moving part is a cut-out of the original
artwork, so text, faces, glasses, suits and name tags are never redrawn.

    python3 src/render.py            # full video -> out/studyolution_promo.mp4
    python3 src/render.py --stills   # a few preview frames -> build/stills/
"""
import argparse
import math
import os
import subprocess

import cv2
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUILD = os.path.join(ROOT, "build")
OUT = os.path.join(ROOT, "out")

FPS = 30
DUR = 8.0
W, H = 1080, 1920          # output canvas (9:16)
PW, PH = 1080, 1440        # poster
OY = (H - PH) // 2         # poster sits in the middle of the canvas
PY = 59.46                 # background grid period (vertical)


# ---------------------------------------------------------------- easing ----
def clamp01(x):
    return min(1.0, max(0.0, x))


def smooth(a, b, t):
    x = clamp01((t - a) / (b - a))
    return x * x * (3 - 2 * x)


def ease_out(x):
    x = clamp01(x)
    return 1 - (1 - x) ** 3


def ease_in(x):
    x = clamp01(x)
    return x ** 3


def ease_in_out(x):
    x = clamp01(x)
    return 4 * x ** 3 if x < 0.5 else 1 - (-2 * x + 2) ** 3 / 2


def bump(a, b, t):
    """0 -> 1 -> 0 between a and b (sine squared)."""
    if t <= a or t >= b:
        return 0.0
    return math.sin(math.pi * (t - a) / (b - a)) ** 2


def idle(t):
    """Envelope for the ambient float: silent on frame 0 and in the final hold."""
    return smooth(0.0, 0.7, t) * (1 - smooth(6.6, 7.3, t))


def pop(t, t0, peak=0.14):
    """Scale >= 1 that springs up and bounces back down to exactly 1."""
    tau = t - t0
    if tau <= 0:
        return 1.0
    if tau < 0.16:
        return 1 + peak * ease_out(tau / 0.16)
    tau -= 0.16
    if tau > 1.0:
        return 1.0
    return 1 + peak * math.exp(-5.5 * tau) * abs(math.cos(11 * tau))


# ---------------------------------------------------------------- layers ----
def soft(mask, grow=0, feather=1.0):
    m = mask.astype(np.uint8)
    if grow:
        m = cv2.dilate(m, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * grow + 1,) * 2))
    return np.clip(cv2.GaussianBlur(m.astype(np.float32), (0, 0), feather), 0, 1)


def bbox(mask, pad):
    ys, xs = np.nonzero(mask)
    return (max(0, xs.min() - pad), max(0, ys.min() - pad),
            min(PW, xs.max() + pad + 1), min(PH, ys.max() + pad + 1))


class Layer:
    """A cut-out of the poster that can be moved with an affine transform."""

    def __init__(self, rgb, alpha, pad=60, pivot=None, hole=None):
        x0, y0, x1, y1 = bbox(alpha > 0.01, pad)
        self.box = (x0, y0, x1, y1)
        self.rgb = rgb[y0:y1, x0:x1].copy()
        self.a = alpha[y0:y1, x0:x1].copy()
        if pivot is None:
            ys, xs = np.nonzero(alpha > 0.5)
            pivot = (xs.mean(), ys.mean())
        self.pivot = pivot
        # where the clean plate must show through while the layer is away
        self.hole = hole

    def matrix(self, dx=0.0, dy=0.0, rot=0.0, sx=1.0, sy=None):
        sy = sx if sy is None else sy
        x0, y0 = self.box[:2]
        px, py = self.pivot[0] - x0, self.pivot[1] - y0
        c, s = math.cos(math.radians(rot)), math.sin(math.radians(rot))
        A = np.array([[c * sx, -s * sy], [s * sx, c * sy]])
        t = np.array([px + dx, py + dy]) - A @ np.array([px, py])
        return np.hstack([A, t[:, None]]).astype(np.float32)

    def draw(self, frame, dx=0.0, dy=0.0, rot=0.0, sx=1.0, sy=None, opacity=1.0):
        x0, y0, x1, y1 = self.box
        M = self.matrix(dx, dy, rot, sx, sy)
        size = (x1 - x0, y1 - y0)
        rgb = cv2.warpAffine(self.rgb, M, size, flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
        a = cv2.warpAffine(self.a, M, size, flags=cv2.INTER_LINEAR)[..., None] * opacity
        dst = frame[y0:y1, x0:x1]
        dst *= 1 - a
        dst += rgb * a

    def shadow(self, frame, dx, dy, sx, strength, blur=9.0):
        """Soft drop shadow under the layer, used while it pops towards the camera."""
        if strength <= 0.002:
            return
        x0, y0, x1, y1 = self.box
        M = self.matrix(dx, dy, 0, sx)
        a = cv2.warpAffine(self.a, M, (x1 - x0, y1 - y0), flags=cv2.INTER_LINEAR)
        a = cv2.GaussianBlur(a, (0, 0), blur)[..., None] * strength
        frame[y0:y1, x0:x1] *= 1 - a * 0.85


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stills", action="store_true")
    args = ap.parse_args()

    L = np.load(os.path.join(BUILD, "layers.npz"))
    img = L["img"].astype(np.float32)
    plate = L["plate"].astype(np.float32)
    plate_obj = L["plate_obj"].astype(np.float32)
    lf = L["lf"].astype(np.float32)
    bg_p = L["bgmask"].astype(np.float32)

    # ---- 9:16 canvas: continue the poster's grid above and below it. ----
    base_canvas = np.zeros((H, W, 3), np.float32)
    base_canvas[OY:OY + PH] = img
    for yc in list(range(0, OY)) + list(range(OY + PH, H)):
        y = yc - OY
        if y < 0:
            ys = y + math.ceil((4 - y) / PY) * PY
            edge, dist = 0, -y
        else:
            ys = y - math.ceil((y - (PH - 5)) / PY) * PY
            edge, dist = PH - 1, y - PH + 1
        y0 = int(math.floor(ys))
        f = ys - y0
        src = plate[y0] * (1 - f) + plate[y0 + 1] * f
        src_lf = lf[y0] * (1 - f) + lf[y0 + 1] * f
        dark = 1 - 0.28 * (dist / OY) ** 1.4
        base_canvas[yc] = src * (lf[edge] * dark) / np.maximum(src_lf, 1)
    # feather the extension into the poster's first/last row so the joins vanish
    for edge_y, sgn in ((OY, -1), (OY + PH - 1, 1)):
        for k in range(1, 4):
            a = 0.5 * (4 - k) / 4
            y = edge_y + sgn * k
            base_canvas[y] = base_canvas[y] * (1 - a) + base_canvas[edge_y] * a
    bg_c = np.ones((H, W), np.float32)
    bg_c[OY:OY + PH] = bg_p

    grey = cv2.cvtColor(base_canvas.astype(np.uint8), cv2.COLOR_RGB2GRAY).astype(np.float32)
    grid_c = np.clip((grey - cv2.GaussianBlur(grey, (0, 0), 3)) / 7, 0, 1) * bg_c
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    radius = np.hypot(xx - W / 2, yy - H * 0.45)
    diag = (xx * 0.42 + yy * 0.9)

    # ---- moving cut-outs (with a clean plate behind them). ----
    def obj(name, **kw):
        m = L["obj_" + name]
        hole = soft(m, grow=4, feather=1.5)
        return Layer(img, soft(m, feather=0.8), hole=hole, **kw)

    cubes_left = obj("cubes_left", pivot=(0, 270))
    cube2 = obj("cube2")
    divide = obj("divide")
    plus = obj("plus")
    atom_big = obj("atom_big", pivot=(1080, 205))
    atom_small = obj("atom_small", pivot=(618, 410))
    ag = obj("ag")
    br = obj("br")
    dna = obj("dna", pivot=(1080, 1225))
    car = obj("car")
    bar = obj("bar", pad=90)
    movers = [cubes_left, cube2, divide, plus, atom_big, atom_small, ag, br, dna, car, bar]

    # ---- in-place pops (scale >= 1, so the original is always covered). ----
    def block_layer(poly, occ, fill, front, pivot):
        rgb = img.copy()
        hidden = poly & occ
        rgb[hidden] = fill
        rgb = np.where(cv2.dilate(hidden.astype(np.uint8), np.ones((3, 3), np.uint8))[..., None] > 0,
                       cv2.GaussianBlur(rgb, (0, 0), 1.0), rgb)
        # everything that sits in front of the block is redrawn on top of it
        return Layer(rgb, soft(poly, feather=0.7), pad=40, pivot=pivot), soft(occ | front, feather=0.8)

    fronts = {
        "online": L["fig_l"] | L["fig_c"] | L["klass"],
        "klass": L["tutor"] | L["fig_r"],
        "tutor": (L["front_l"] & ~L["tutor"]) | L["front_r"],
    }
    blocks = []
    for poly, occ, fill, t0, pivot, peak in (
        # Online grows from its top edge so it never covers the tagline above it
        ("online", "occ_online", (255, 255, 255), 2.0, (387, 484), 0.11),
        ("klass", "occ_class", (253, 233, 98), 2.38, None, 0.11),
        ("tutor", "occ_tutor", (155, 14, 18), 2.76, None, 0.11),
    ):
        lay, occ_a = block_layer(L[poly], L[occ], fill, fronts[poly], pivot)
        blocks.append((lay, occ_a, t0, peak))

    ribbon = Layer(img, soft(L["ribbon"], feather=0.8), pad=30, pivot=(805, 360))
    rib_mask = soft(L["ribbon"], feather=0.8)

    figures = []
    for fig, front, pivot, t0, t1, amt in (
        ("fig_c", "front_c", (735, 700), 4.0, 5.7, 0.028),
        ("fig_l", "front_l", (95, 890), 4.25, 5.95, 0.032),
        ("fig_r", "front_r", (1025, 965), 4.5, 6.2, 0.03),
    ):
        lay = Layer(img, soft(L[fig], feather=0.8), pad=30, pivot=pivot)
        figures.append((lay, soft(L[front], grow=1, feather=0.8), t0, t1, amt))

    pins = [
        (Layer(img, soft(L["pin_l"], feather=0.7), pad=70, pivot=(297, 932)), 4.55),
        (Layer(img, soft(L["pin_r"], feather=0.7), pad=70, pivot=(778, 978)), 4.95),
    ]

    diff = np.abs(img - plate).max(2)
    stars = []
    for (x0, y0, x1, y1), t0 in (((303, 370, 340, 406), 0.5), ((641, 310, 674, 344), 1.1),
                                 ((96, 876, 150, 932), 1.6), ((454, 950, 488, 984), 0.85)):
        m = np.zeros((PH, PW), bool)
        m[y0:y1, x0:x1] = diff[y0:y1, x0:x1] > 35
        stars.append((Layer(img, soft(m, grow=1, feather=0.7), pad=20), t0))

    rng = np.random.default_rng(7)
    sparkles = [(rng.uniform(40, W - 40), rng.uniform(40, H - 40), rng.uniform(0.3, 6.5), rng.uniform(5, 11))
                for _ in range(14)]
    sparkles = [s for s in sparkles if bg_c[int(s[1]), int(s[0])] > 0.9]
    dust = [(rng.uniform(0, W), rng.uniform(0, H), rng.uniform(1.5, 4.5), rng.uniform(12, 40), rng.uniform(0, 6.28))
            for _ in range(46)]

    def glint(canvas, cx, cy, size, k):
        if k <= 0.01:
            return
        r = int(size * 3)
        x0, x1 = int(max(0, cx - r)), int(min(W, cx + r))
        y0, y1 = int(max(0, cy - r)), int(min(H, cy + r))
        gx = xx[y0:y1, x0:x1] - cx
        gy = yy[y0:y1, x0:x1] - cy
        core = np.exp(-(gx ** 2 + gy ** 2) / (2 * (size * 0.35) ** 2))
        cross = np.exp(-np.abs(gx) / (size * 0.12)) * np.exp(-np.abs(gy) / size) + \
            np.exp(-np.abs(gy) / (size * 0.12)) * np.exp(-np.abs(gx) / size)
        canvas[y0:y1, x0:x1] += (np.clip(core + cross, 0, 1.4) * 255 * k)[..., None] * np.array([1, 0.97, 0.85])

    # ------------------------------------------------------------ frame ----
    def frame_at(t):
        p = img.copy()

        # where movers are away from home, show the clean plate
        st = {
            "cubes_left": dict(dy=-7 * math.sin(2 * math.pi * t / 2.6) * idle(t),
                               rot=1.6 * math.sin(2 * math.pi * t / 3.1) * idle(t)),
            "cube2": dict(dy=-10 * math.sin(2 * math.pi * (t / 2.2)) * idle(t),
                          rot=-6 * math.sin(2 * math.pi * t / 2.9) * idle(t)),
            "divide": dict(dy=-9 * math.sin(2 * math.pi * t / 1.9) * idle(t),
                           rot=12 * math.sin(2 * math.pi * t / 2.4) * idle(t)),
            "plus": dict(dx=4 * math.sin(2 * math.pi * t / 2.3) * idle(t),
                         dy=-8 * math.sin(2 * math.pi * t / 1.7) * idle(t),
                         rot=-20 * math.sin(2 * math.pi * t / 2.6) * idle(t)),
            "atom_big": dict(rot=-7 * math.sin(2 * math.pi * t / 3.4) * idle(t),
                             sx=1 - 0.05 * math.sin(math.pi * t / 1.6) ** 2 * idle(t)),
            "atom_small": dict(rot=-360 * ease_in_out((t - 0.3) / 3.2) if t < 3.5 else 0.0),
            "ag": dict(dy=-9 * math.sin(2 * math.pi * (t - 4.0) / 1.25) * bump(4.0, 6.5, t) ** 0.5,
                       rot=5 * math.sin(2 * math.pi * (t - 4.0) / 1.6) * bump(4.0, 6.5, t) ** 0.5),
            "br": dict(dy=-9 * math.sin(2 * math.pi * (t - 4.2) / 1.25) * bump(4.2, 6.7, t) ** 0.5,
                       rot=-5 * math.sin(2 * math.pi * (t - 4.2) / 1.6) * bump(4.2, 6.7, t) ** 0.5),
            "dna": dict(sx=1 - 0.16 * abs(math.sin(2 * math.pi * clamp01((t - 5.9) / 1.0))),
                        rot=3 * math.sin(2 * math.pi * clamp01((t - 5.9) / 1.0)),
                        dy=-6 * bump(5.9, 6.9, t)),
        }
        # car: rolls back up the ramp, then drives forward and settles
        u = np.array([1.0, 0.135]) / math.hypot(1, 0.135)
        if t < 6.0 or t > 7.15:
            d = 0.0
        elif t < 6.35:
            d = -30 * ease_in_out((t - 6.0) / 0.35)
        elif t < 6.85:
            d = -30 + 37 * ease_in((t - 6.35) / 0.5) ** 0.6
        else:
            d = 7 * (1 - ease_out((t - 6.85) / 0.3))
        st["car"] = dict(dx=d * u[0], dy=d * u[1] - 2.5 * abs(math.sin(9 * (t - 6.0))) * bump(6.0, 7.15, t))
        # contact bar: dips out, then slides up into place
        if 6.05 <= t < 6.3:
            k = ease_in((t - 6.05) / 0.25)
            st["bar"] = dict(dy=26 * k, opacity=1 - k)
        elif 6.3 <= t < 7.0:
            k = clamp01((t - 6.3) / 0.7)
            back = 1 + 2.2 * (k - 1) ** 3 + 1.2 * (k - 1) ** 2
            st["bar"] = dict(dy=70 * (1 - back), opacity=min(1.0, k * 2.5))
        else:
            st["bar"] = {}

        names = ["cubes_left", "cube2", "divide", "plus", "atom_big", "atom_small", "ag", "br", "dna", "car", "bar"]
        active = []
        for name, lay in zip(names, movers):
            s = st.get(name, {})
            if any(abs(v - (1.0 if k in ("sx", "opacity") else 0.0)) > 1e-3 for k, v in s.items()):
                active.append((lay, s))
                x0, y0, x1, y1 = lay.box
                hole = lay.hole[y0:y1, x0:x1][..., None]
                p[y0:y1, x0:x1] = p[y0:y1, x0:x1] * (1 - hole) + plate_obj[y0:y1, x0:x1] * hole
        for lay, s in active:
            lay.draw(p, **s)

        # title blocks bounce (scale only ever >= 1)
        for lay, occ_a, t0, peak in blocks:
            s = pop(t, t0, peak)
            if s > 1.0005:
                k = (s - 1) / peak
                lay.shadow(p, 8 * k, 12 * k, s, 0.38 * k, blur=10)
                lay.draw(p, sx=s)
                x0, y0, x1, y1 = lay.box
                o = occ_a[y0:y1, x0:x1][..., None]
                p[y0:y1, x0:x1] = p[y0:y1, x0:x1] * (1 - o) + img[y0:y1, x0:x1] * o

        # ribbon: small pop and a light that travels along the arc
        rs = pop(t, 2.95, 0.07)
        if rs > 1.0005:
            ribbon.draw(p, sx=rs)
        sh = clamp01((t - 2.95) / 0.9)
        if 0 < sh < 1:
            ang = np.degrees(np.arctan2(yy[OY:OY + PH] - OY - 450, xx[OY:OY + PH] - 805))
            centre = -170 + 160 * ease_in_out(sh)
            band = np.exp(-((ang - centre) / 9) ** 2) * math.sin(math.pi * sh)
            p += (band * rib_mask * 150)[..., None]

        # people: a gentle lift / lean, anchored low so the cut-out only grows
        for lay, front, t0, t1, amt in figures:
            k = bump(t0, t1, t)
            if k > 1e-3:
                lay.draw(p, sx=1 + amt * k, sy=1 + amt * 1.15 * k)
                x0, y0, x1, y1 = lay.box
                f = front[y0:y1, x0:x1][..., None]
                p[y0:y1, x0:x1] = p[y0:y1, x0:x1] * (1 - f) + img[y0:y1, x0:x1] * f

        # pins: lift towards the camera, then drop onto the notes
        for lay, t0 in pins:
            tau = t - t0
            if 0 < tau < 0.75:
                if tau < 0.22:
                    s = 1 + 0.55 * ease_out(tau / 0.22)
                elif tau < 0.44:
                    s = 1.55 - 0.55 * ease_in((tau - 0.22) / 0.22)
                else:
                    s = 1 + 0.07 * math.sin(math.pi * (tau - 0.44) / 0.31)
                k = (s - 1) / 0.55
                lay.shadow(p, 22 * k, 26 * k, s, 0.45 * k, blur=4 + 6 * k)
                lay.draw(p, sx=s)

        # stars twinkle
        for lay, t0 in stars:
            k = sum(bump(t0 + n * 2.1, t0 + n * 2.1 + 0.7, t) for n in range(4))
            if t > 7.3:
                k = 0
            if k > 1e-3:
                lay.draw(p, sx=1 + 0.45 * k, rot=25 * k)

        # ------------------------------------------- canvas + camera --------
        c = base_canvas.copy()
        c[OY:OY + PH] = p

        # background shimmer: grid lines pulse in a slow ring + light sweep
        shim = 0.35 * smooth(0, 0.6, t) * (1 - smooth(6.9, 7.4, t)) + 0.65 * bump(0.0, 2.4, t)
        if shim > 1e-3:
            wave = 0.5 + 0.5 * np.sin(radius * 0.011 - t * 4.2)
            c += (grid_c * wave * 55 * shim)[..., None] * np.array([0.75, 0.9, 1.0])
        if 0.15 < t < 2.1:
            pos = -300 + 2600 * ease_in_out((t - 0.15) / 1.95)
            band = np.exp(-((diag - pos) / 120) ** 2)
            c += (band * (0.65 * bg_c + 0.18) * 70)[..., None] * np.array([0.85, 0.93, 1.0])
        if 6.9 < t < 7.6:
            x0, y0, x1, y1 = bar.box
            pos = x0 - 100 + (x1 - x0 + 200) * ease_in_out((t - 6.9) / 0.7)
            sl = slice(OY + y0, OY + y1)
            band = np.exp(-(((xx[sl, x0:x1] + (yy[sl, x0:x1] - OY - y0) * 0.6) - pos) / 40) ** 2)
            c[sl, x0:x1] += (band * bar.a * 120)[..., None]

        # floating dust + sparkles on the background only
        dk = smooth(0.2, 1.2, t) * (1 - smooth(6.8, 7.35, t))
        if dk > 1e-3:
            layer = np.zeros((H, W), np.float32)
            for x, y, r, v, ph in dust:
                yy0 = (y - v * t) % H
                xx0 = x + 10 * math.sin(t * 0.8 + ph)
                a = 0.35 * (0.6 + 0.4 * math.sin(t * 2.3 + ph))
                cv2.circle(layer, (int(xx0 * 4), int(yy0 * 4)), int(r * 4), a, -1, cv2.LINE_AA, shift=2)
            layer = cv2.GaussianBlur(layer, (0, 0), 1.6) * bg_c * dk
            c += (layer * 255)[..., None] * np.array([0.8, 0.9, 1.0])
            for x, y, t0, size in sparkles:
                glint(c, x, y, size, 0.55 * bump(t0, t0 + 0.8, t) * dk)
        for lay, t0 in stars:
            k = sum(bump(t0 + n * 2.1, t0 + n * 2.1 + 0.7, t) for n in range(4)) * (t <= 7.3)
            px, py = lay.pivot
            glint(c, px, py + OY, 9, 0.5 * k)

        # camera: slow push-in, then pull back to the full poster for the hold
        z = 1 + 0.07 * ease_in_out(t / 2.0) + 0.02 * clamp01((t - 2.0) / 4.8) \
            - 0.09 * ease_in_out((t - 6.8) / 0.6)
        if abs(z - 1) > 1e-4:
            cx, cy = W / 2, H * 0.48
            M = np.float32([[z, 0, cx - z * cx], [0, z, cy - z * cy]])
            c = cv2.warpAffine(c, M, (W, H), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT)
        return np.clip(c, 0, 255).astype(np.uint8)

    if args.stills:
        d = os.path.join(BUILD, "stills")
        os.makedirs(d, exist_ok=True)
        for t in (0.0, 1.0, 2.15, 2.55, 3.35, 4.75, 5.15, 6.2, 6.55, 7.0, 7.99):
            cv2.imwrite(os.path.join(d, f"t{t:05.2f}.png"), cv2.cvtColor(frame_at(t), cv2.COLOR_RGB2BGR))
        print("stills ->", d)
        return

    os.makedirs(OUT, exist_ok=True)
    audio = os.path.join(BUILD, "audio.wav")
    subprocess.run(["python3", os.path.join(ROOT, "src", "audio.py"), audio], check=True)
    out = os.path.join(OUT, "studyolution_promo.mp4")
    ff = subprocess.Popen([
        "ffmpeg", "-y", "-loglevel", "error",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
        "-i", audio,
        "-c:v", "libx264", "-preset", "slow", "-crf", "15", "-pix_fmt", "yuv420p",
        "-tune", "animation", "-profile:v", "high", "-level", "4.2",
        "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", out,
    ], stdin=subprocess.PIPE)
    n = int(round(DUR * FPS))
    for i in range(n):
        ff.stdin.write(frame_at(i / FPS).tobytes())
        if i % 30 == 0:
            print(f"frame {i}/{n}", flush=True)
    ff.stdin.close()
    ff.wait()
    print("wrote", out)


if __name__ == "__main__":
    main()
