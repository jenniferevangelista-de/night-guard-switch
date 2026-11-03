"""PRE-EXISTING: copied from github.com/jenniferevangelista-de/night-guard (video/ng_sloth.py).

Snoozy / Soneca: a kawaii sloth dressed as a night watchman. He narrates the film.

Kawaii look: round body, thick outline, big glossy eyes, blush, watchman cap with a moon badge. The mouth follows the narration loudness; he blinks slowly and yawns at the end.
  python video/ng_sloth.py   -> video/review_en/sloth_sheet.png
"""
import math
import random
import sys
from pathlib import Path

from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from palito import INK, dr, font, jit, wcircle, wline, wrect  # noqa: E402,F401

FUR = (152, 116, 84); FUR_D = (112, 82, 58); MASK = (236, 214, 178); PATCH = (88, 60, 42)
NAVY = (38, 50, 108); NAVY_D = (26, 34, 78); GEM = (60, 200, 235); GOLD = (255, 211, 110); WHITE = (255, 255, 255)


LINE = (42, 32, 72); FUR_K = (192, 152, 114); FACE = (247, 234, 210); BELLY = (244, 232, 210); PATCH_K = (116, 84, 62)
BLUSH = (245, 150, 175, 150); TONGUE = (240, 120, 140)


def _rot_ellipse(cx, cy, rx, ry, ang, n=36):
    c, s_ = math.cos(ang), math.sin(ang)
    return [(cx + rx * math.cos(2 * math.pi * k / n) * c - ry * math.sin(2 * math.pi * k / n) * s_,
             cy + rx * math.cos(2 * math.pi * k / n) * s_ + ry * math.sin(2 * math.pi * k / n) * c) for k in range(n)]


def sloth(img, t, cx, by, h=420, m=0.0, mood="talk", wave=0.0, seed=7000, emo="happy"):
    """Draw Snoozy (kawaii style: round body, thick outline, big glossy eyes, blush) with feet at (cx, by).
    m: mouth 0..1 · mood: talk | listen | sleep | yawn · wave: 0..1 right paw greeting · emo: happy | angry."""
    SS = 2                                             # draw at 2x, then downscale for smooth edges
    k = SS * h / 420.0
    W_, H_ = int(420 * k), int(440 * k)
    lay = Image.new("RGBA", (W_, H_), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    P = lambda x, y: (x * k, y * k)
    B = lambda x0, y0, x1, y1: (x0 * k, y0 * k, x1 * k, y1 * k)
    lw = max(2, int(7 * k))
    bob = math.sin(dr(t) / 12 * 2.2) * 3                # lazy bounce on twos

    d.ellipse(B(110, 418, 310, 436), fill=(0, 0, 0, 40))                                   # soft shadow
    for x0 in (128, 222):                                                                  # tiny feet
        d.ellipse(B(x0, 392, x0 + 70, 424), fill=FUR_K, outline=LINE, width=lw)
    # left paw with a little flashlight
    d.polygon([P(*p) for p in _rot_ellipse(64, 292 + bob, 26, 44, math.radians(28))], fill=FUR_K, outline=LINE, width=lw)
    d.rounded_rectangle(B(34, 318 + bob, 68, 352 + bob), radius=int(6 * k), fill=(110, 112, 128), outline=LINE, width=max(2, lw // 2))
    d.polygon([P(38, 352 + bob), P(64, 352 + bob), P(84, 400 + bob), P(18, 400 + bob)], fill=(255, 238, 160, 200))
    # right paw: down, or waving hello
    ang = math.radians(-25 + 130 * wave + 14 * wave * math.sin(dr(t) / 12 * 6))
    ax, ay = 336, 292 + bob - 40 * wave
    d.polygon([P(*p) for p in _rot_ellipse(ax + 30 * wave, ay - 20 * wave, 26, 44, -ang)], fill=FUR_K, outline=LINE, width=lw)
    # round body + belly
    d.ellipse(B(52, 112 + bob, 348, 408), fill=FUR_K, outline=LINE, width=lw)
    d.ellipse(B(128, 300 + bob, 272, 398), fill=BELLY)
    # face mask, droopy eye patches, glossy eyes, blush
    d.ellipse(B(92, 168 + bob, 308, 312 + bob), fill=FACE)
    for sx, ex in ((-1, 152), (1, 248)):
        ey = 228 + bob
        d.polygon([P(*p) for p in _rot_ellipse(ex + sx * 4, ey + 6, 44, 30, math.radians(-sx * 28))], fill=PATCH_K)
        if mood == "sleep" or (mood != "yawn" and (t % 4.3) < 0.16):
            d.arc(B(ex - 22, ey - 8, ex + 22, ey + 18), 20, 160, fill=LINE, width=lw)
        else:
            d.ellipse(B(ex - 25, ey - 26, ex + 25, ey + 26), fill=LINE)
            d.ellipse(B(ex - 15, ey - 18, ex - 1, ey - 4), fill=(255, 255, 255))
            d.ellipse(B(ex + 6, ey + 6, ex + 14, ey + 14), fill=(255, 255, 255))
    for x0 in (102, 262):
        d.ellipse(B(x0, 262 + bob, x0 + 38, 280 + bob), fill=BLUSH if emo == "happy" else (235, 90, 90, 120))
    if emo == "angry" and mood != "sleep":             # frowning brows + anger mark
        for ex, sx in ((152, -1), (248, 1)):
            d.line([P(ex + sx * 30, 186 + bob), P(ex - sx * 18, 200 + bob)], fill=LINE, width=int(lw * 1.4))
        ax0, ay0 = 330, 120 + bob
        for a0 in (0, 90, 180, 270):
            d.arc(B(ax0 - 18, ay0 - 18, ax0 + 18, ay0 + 18), a0 + 20, a0 + 70, fill=(220, 50, 60), width=lw)
    d.ellipse(B(188, 252 + bob, 212, 266 + bob), fill=LINE)                                 # nose
    my = 272 + bob
    if mood == "yawn":
        d.ellipse(B(182, my - 2, 218, my + 40), fill=LINE); d.ellipse(B(190, my + 20, 210, my + 36), fill=TONGUE)
    elif m > 0.06 and emo == "angry":
        o = 0.35 + 0.65 * min(1.0, m)
        d.chord(B(180, my - 4, 220, my + 10 + 30 * o), 180, 360, fill=LINE)          # grumpy open mouth
    elif m > 0.06:
        o = 0.35 + 0.65 * min(1.0, m)
        d.chord(B(178, my - 8, 222, my + 34 * o), 0, 180, fill=LINE)
        d.chord(B(188, my + 4 * o, 212, my + 30 * o), 0, 180, fill=TONGUE)
    elif emo == "angry":
        d.arc(B(182, my + 2, 218, my + 24), 200, 340, fill=LINE, width=lw)     # frown
    else:
        d.arc(B(182, my - 14, 218, my + 10), 20, 160, fill=LINE, width=lw)
    # watchman cap with a gold moon badge
    d.chord(B(78, 52 + bob, 322, 252 + bob), 180, 360, fill=NAVY, outline=LINE, width=lw)
    d.rounded_rectangle(B(66, 140 + bob, 346, 170 + bob), radius=int(14 * k), fill=NAVY_D, outline=LINE, width=lw)
    d.ellipse(B(178, 82 + bob, 222, 126 + bob), fill=GOLD, outline=LINE, width=max(2, lw // 2))
    d.ellipse(B(190, 78 + bob, 228, 118 + bob), fill=NAVY)                                   # crescent cut
    if mood == "sleep":
        for i in range(3):
            zt = (t * 0.6 + i * 0.33) % 1
            d.text(P(330 + zt * 50, 120 - zt * 100), "z", fill=NAVY, font=font("impact.ttf", int((26 + 22 * zt) * k)), anchor="mm")
    w2, h2 = int(W_ / SS), int(H_ / SS)
    lay = lay.resize((w2, h2), Image.LANCZOS)
    img.paste(lay, (int(cx - w2 / 2), int(by - h2 * 424 / 440)), lay)


def kid_in_bed(d, t, label=None, label_font=None):
    """A kid asleep under a blanket: whole body, not just the head."""
    wrect(d, 140, 650, 780, 760, t, 1900, 8, fill=(244, 244, 250))            # mattress
    wline(d, [(140, 760), (140, 900)], t, 1901, 8); wline(d, [(780, 760), (780, 900)], t, 1902, 8)
    wline(d, [(140, 560), (140, 760)], t, 1909, 8)                              # headboard
    wrect(d, 160, 600, 320, 652, t, 1903, 6, fill=WHITE)                        # pillow
    wline(d, [(300, 610), (470, 622), (640, 628)], t, 1905, 8)                  # torso and legs under the blanket
    wline(d, [(640, 628), (700, 612)], t, 1906, 7); wline(d, [(640, 628), (705, 632)], t, 1907, 7)   # feet
    blanket = [(320, 596), (430, 588), (560, 600), (690, 606), (705, 652), (318, 652)]
    d.polygon([jit(p, t, 1910 + i, 2) for i, p in enumerate(blanket)], fill=(170, 195, 245))
    wline(d, blanket + [blanket[0]], t, 1911, 6)
    for i in range(4):                                                          # little stars on the blanket
        sx = 380 + i * 80; d.ellipse((sx - 5, 620 - 5, sx + 5, 620 + 5), fill=(255, 211, 110))
    wline(d, [(330, 612), (400, 600), (470, 610)], t, 1912, 7)                  # arm resting on top
    wcircle(d, 255, 588, 50, t, 1904, 7, fill=(247, 242, 230))                   # head on the pillow
    d.arc((218, 576, 248, 596), 20, 160, fill=INK, width=5); d.arc((262, 576, 292, 596), 20, 160, fill=INK, width=5)
    d.arc((236, 598, 276, 620), 20, 160, fill=INK, width=5)


if __name__ == "__main__":
    from palito import paper
    img = paper().copy()
    for i, (mood, m, wv, emo) in enumerate([("listen", 0.0, 0.0, "angry"), ("talk", 0.7, 0.0, "angry"), ("talk", 0.4, 1.0, "happy"),
                                            ("listen", 0, 0, "happy"), ("yawn", 0, 0, "happy"), ("sleep", 0, 0, "happy")]):
        sloth(img, i * 0.3, 170 + i * 320, 900, 420, m, mood, wv, emo=emo)
    out = HERE / "review_en"; out.mkdir(exist_ok=True)
    img.save(out / "sloth_sheet.png"); print("ok")
