"""Props shared by the Night Guard film scenes: speech bubbles, the moon window, the desk, the shield
mascot, the phone, cards, checkmarks and stamps.

PRE-EXISTING: copied verbatim from github.com/jenniferevangelista-de/night-guard (video/ng_film.py).
"""
import math
import random
import textwrap
from functools import lru_cache

import numpy as np
from PIL import Image, ImageDraw

from palito import INK, RED, eio, eout, font, jit, text, wline, wrect  # noqa: F401

NIGHT = (38, 50, 108); MOON = (255, 211, 110); GREEN = (52, 160, 100); WHITE = (255, 255, 255)
SOFT = (120, 112, 125)


@lru_cache(maxsize=4)
def rms_env(path):
    import soundfile as sf
    a, sr = sf.read(str(path), dtype="float32"); a = a.mean(1) if a.ndim > 1 else a; hop = sr // 12
    r = np.array([np.sqrt(np.mean(a[j:j + hop] ** 2)) for j in range(0, len(a), hop)])
    return (r / (r.max() or 1)).tolist()


def level(path, t0, t):
    e = rms_env(str(path)); k = int((t - t0) * 12)
    return e[k] if 0 <= k < len(e) else 0.0


# ------------------------------------------------------------------ props
def bubble(d, t, x, y, s, seed, k=1.0, who="Alex_17", col=WHITE, size=40):
    if k <= 0: return
    f = font("segoeprb.ttf", size); w = d.textlength(s, font=f) + 60; h = size + 50
    sc = eout(k); w2, h2 = w * sc, h * sc
    wrect(d, x, y, x + w2, y + h2, t, seed, 5, fill=col)
    wline(d, [(x + 30 * sc, y + h2), (x + 18 * sc, y + h2 + 26 * sc), (x + 56 * sc, y + h2)], t, seed + 7, 5)
    if k >= 0.6:
        text(d, who, x + 14, y - 22, 26, SOFT, "lm")
        text(d, s, x + 30, y + h / 2, size, INK, "lm")


def moon_window(d, t, x0=170, y0=140, x1=520, y1=470):
    d.rectangle((x0, y0, x1, y1), fill=NIGHT)
    wrect(d, x0, y0, x1, y1, t, 400, 8)
    wline(d, [((x0 + x1) / 2, y0), ((x0 + x1) / 2, y1)], t, 401, 6); wline(d, [(x0, (y0 + y1) / 2), (x1, (y0 + y1) / 2)], t, 402, 6)
    cx, cy = x0 + 230, y0 + 100
    d.ellipse((cx - 55, cy - 55, cx + 55, cy + 55), fill=MOON); d.ellipse((cx - 25, cy - 70, cx + 75, cy + 35), fill=NIGHT)
    r = random.Random(4)
    for i in range(9):
        sx, sy = r.uniform(x0 + 20, x1 - 20), r.uniform(y0 + 20, y1 - 20)
        if abs(sx - cx) < 70 and abs(sy - cy) < 70: continue
        tw = 3 + 3 * abs(math.sin(t * 2 + i))
        d.ellipse((sx - tw, sy - tw, sx + tw, sy + tw), fill=WHITE)


def desk_set(d, t, glow=1.0):
    wline(d, [(560, 760), (1240, 760)], t, 101, 9)
    wline(d, [(600, 760), (600, 960)], t, 102, 8); wline(d, [(1200, 760), (1200, 960)], t, 103, 8)
    wline(d, [(80, 960), (1840, 960)], t, 104, 6)
    wrect(d, 790, 738, 960, 758, t, 105, 5, fill=(225, 225, 225))
    wline(d, [(640, 812), (790, 812)], t, 106, 8)
    wline(d, [(650, 812), (650, 960)], t, 107, 7); wline(d, [(780, 812), (780, 960)], t, 108, 7)
    wline(d, [(650, 812), (640, 660)], t, 109, 7)
    fill = tuple(int(a * (1 - glow) + b * glow) for a, b in zip((230, 236, 245), (150, 210, 255)))
    wrect(d, 860, 470, 1180, 690, t, 110, 8, fill=fill)
    wline(d, [(1020, 690), (1020, 760)], t, 111, 8); wline(d, [(960, 760), (1080, 760)], t, 112, 8)


def shield(d, t, cx, cy, s=1.0, k=1.0, eyes="open", seed=500):
    """Night Guard mascot: a shield with a moon and two eyes. k draws it on (0..1)."""
    pts = [(cx, cy - 170 * s), (cx + 140 * s, cy - 120 * s), (cx + 130 * s, cy + 30 * s), (cx, cy + 170 * s),
           (cx - 130 * s, cy + 30 * s), (cx - 140 * s, cy - 120 * s), (cx, cy - 170 * s)]
    if k >= 1:
        d.polygon([jit(p, t, seed + i, 2) for i, p in enumerate(pts[:-1])], fill=NIGHT)
        mx, my = cx - 30 * s, cy - 40 * s
        d.ellipse((mx - 50 * s, my - 50 * s, mx + 50 * s, my + 50 * s), fill=MOON)
        d.ellipse((mx - 20 * s, my - 65 * s, mx + 70 * s, my + 30 * s), fill=NIGHT)
        ey = cy + 40 * s
        for ex in (cx - 40 * s, cx + 40 * s):
            if eyes == "sleep": d.arc((ex - 18 * s, ey - 10 * s, ex + 18 * s, ey + 14 * s), 20, 160, fill=WHITE, width=max(3, int(6 * s)))
            else: d.ellipse((ex - 12 * s, ey - 12 * s, ex + 12 * s, ey + 12 * s), fill=WHITE)
        wline(d, pts, t, seed, int(9 * s) or 4)
    else:                                                  # drawing on: partial outline
        n = max(2, int(len(pts) * eio(k)) + 1)
        wline(d, pts[:n], t, seed, int(9 * s) or 4)


def speaker(d, t, x, y, lvl):
    wline(d, [(x, y - 20), (x + 22, y - 20), (x + 50, y - 46), (x + 50, y + 46), (x + 22, y + 20), (x, y + 20), (x, y - 20)], t, 600, 6)
    for i in range(3):
        if lvl > 0.12 + i * 0.25:
            r = 70 + i * 32; d.arc((x + 50 - r, y - r, x + 50 + r, y + r), -40, 40, fill=RED, width=7)


def phone(d, t, x, y, k_note, lines):
    wrect(d, x, y, x + 480, y + 720, t, 700, 9, fill=(250, 250, 252))
    wline(d, [(x + 130, y + 30), (x + 200, y + 30)], t, 701, 6)
    if k_note > 0:
        yy = y + 70 + (1 - eout(k_note)) * -60
        wrect(d, x + 22, yy, x + 458, yy + 150, t, 702, 5, fill=(255, 240, 240))
        text(d, "Night Guard", x + 40, yy + 30, 30, NIGHT, "lm", "impact.ttf")
        for i, ln in enumerate(lines):
            text(d, ln, x + 40, yy + 70 + i * 34, 28, INK if i else RED, "lm")


def card(d, t, x, y, k, title, line1, line2, col, seed):
    if k <= 0: return
    s = eout(k); w, h = 700 * s, 300 * s; cx, cy = x + 350, y + 150
    wrect(d, cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2, t, seed, 7, fill=(255, 252, 242))
    if k > 0.7:
        d.rectangle((cx - w / 2 + 8, cy - h / 2 + 8, cx + w / 2 - 8, cy - h / 2 + 22), fill=col)
        text(d, title, cx, cy - 70, 76, col, "mm", "impact.ttf")
        text(d, line1, cx, cy + 20, 40, INK); text(d, line2, cx, cy + 80, 36, SOFT)


def check(d, t, x, y, k, label, seed):
    wrect(d, x, y - 22, x + 44, y + 22, t, seed, 5, fill=WHITE)
    if k > 0:
        wline(d, [(x + 8, y), (x + 20, y + 14), (x + 20 + 30 * eout(k), y + 14 - 40 * eout(k))], t, seed + 3, 7, GREEN)
    text(d, label, x + 70, y, 38, INK, "lm")


def stamp(img, s, cx, cy, ang, col=RED, size=80):
    f = font("impact.ttf", size); im = Image.new("RGBA", (int(len(s) * size * 0.62) + 60, size + 50), (0, 0, 0, 0))
    dd = ImageDraw.Draw(im); dd.rectangle((6, 6, im.width - 6, im.height - 6), outline=col + (255,), width=8)
    dd.text((im.width / 2, im.height / 2), s, font=f, fill=col + (255,), anchor="mm")
    im = im.rotate(ang, expand=True, resample=Image.BICUBIC); img.paste(im, (int(cx - im.width / 2), int(cy - im.height / 2)), im)


def kid_wrap(s, width=34):
    return textwrap.wrap(s, width)


# ------------------------------------------------------------------ scenes
