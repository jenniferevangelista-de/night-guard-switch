"""Night Guard Family Room film (paper style), built on the Night Guard film.

The scenes intro, night, stat, fast, platforms, parents, guard, alert, family and peace, the subtitles, the drama
grade and Snoozy in the corner are PRE-EXISTING: copied from github.com/jenniferevangelista-de/night-guard
(video/ng_film_en.py). New for this project: hello (Jennifer), after, room, helper, decide, kid, threat, tech and end.

  python video/film.py 5 20 40      -> review frames in video/work/review/
  python video/film_audio.py && python video/film_render.py   -> video/out/night_guard_family_room_film.mp4
"""
import json
import math
import random
import sys
import textwrap
from functools import lru_cache
from pathlib import Path

from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "ng"))
sys.path.insert(0, str(HERE.parent))
from ng_film_helpers import (GREEN, MOON, NIGHT, SOFT, WHITE, bubble, check, desk_set, moon_window,  # noqa: E402
                             phone, rms_env, shield, speaker, stamp)
from palito import FPS, H, INK, RED, W, dr, eio, eout, font, jit, paper, poof, seg, stick, text, wcircle, wline, wrect  # noqa: E402,F401
from nightguard.signals import SIGNALS  # noqa: E402
from ng_sloth import kid_in_bed, sloth  # noqa: E402

WORK = HERE / "work"


def _mp3_dur(p):
    import subprocess
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(p)],
                                capture_output=True, text=True).stdout)


FAMILY_FILE = HERE / "ng" / "audio" / "family.mp3"
ALERT_EXTRA = 1.6 + _mp3_dur(FAMILY_FILE) + 0.3   # room for the warning AND the "tell your parents" line   # room for the 11.4 s spoken warning
SARAH_FILE = HERE / "ng" / "audio" / "secrecy.mp3"
PANEL = (29, 37, 80); PANEL2 = (40, 52, 110)


@lru_cache(maxsize=1)
def timeline():
    tl = json.loads((WORK / "film_timeline.json").read_text(encoding="utf-8"))
    out, shift = {}, 0.0
    for s in tl["scenes"]:
        s = dict(s); s["start"] += shift
        if s["id"] == "alert":
            s["end"] += ALERT_EXTRA; shift = ALERT_EXTRA
        else:
            s["end"] += shift
        out[s["id"]] = s
    return out


def S(sid): return timeline()[sid]


DUR = round(S("end")["end"] + 0.6, 2)
SARAH_AT = round(S("alert")["start"] + S("alert")["voice_dur"] + 0.2, 2)
FAMILY_AT = round(SARAH_AT + _mp3_dur(SARAH_FILE) + 0.3, 2)
MUSIC_SWITCH = S("guard")["start"]           # drama -> joy when Night Guard appears


VOZ = WORK / "film_voice"


def narr_level(t):
    """Loudness of the narration at time t (drives Snoozy's mouth); None when nobody narrates."""
    for s in timeline().values():
        if s["start"] <= t < s["start"] + s["voice_dur"]:
            e = rms_env(str(VOZ / s["voice"])); k = int((t - s["start"]) * 12)
            m = e[k] if 0 <= k < len(e) else 0.0
            return 0.0 if m < 0.12 else min(1.0, m * 1.25)
    return None


def level(path, t0, t):
    e = rms_env(str(path)); k = int((t - t0) * 12)
    return e[k] if 0 <= k < len(e) else 0.0


@lru_cache(maxsize=1)
def subs():
    out = []
    for s in timeline().values():
        parts = [p.strip() for p in s["line"].replace(": ", ":|").replace(". ", ".|").split("|") if p.strip()]
        merged, cur = [], ""
        for p in parts:
            if cur and len(cur) + len(p) > 68: merged.append(cur); cur = p
            else: cur = (cur + " " + p).strip()
        merged.append(cur)
        final = []
        for p in merged:                                   # very long sentences: split at commas
            while len(p) > 80 and ", " in p[20:]:
                i = p.rfind(", ", 0, 75); i = i if i > 20 else p.find(", ", 20)
                final.append(p[:i + 1]); p = p[i + 2:]
            final.append(p)
        total = sum(len(p) for p in final); t = s["start"]
        for p in final:
            d = s["voice_dur"] * len(p) / total; out.append((t, t + d + 0.2, p)); t += d
    return out


def subtitle(d, t):
    for a, b, s in subs():
        if a <= t < b:
            f = font("segoeprb.ttf", 40); w = d.textlength(s, font=f)
            d.rounded_rectangle((W / 2 - w / 2 - 24, 1002, W / 2 + w / 2 + 24, 1062), 18, fill=(255, 251, 240))
            text(d, s, W / 2, 1031, 40, INK); return


def dark_overlay(img, k):
    """Drama grade for the first act: darker, colder paper that lifts when the guard arrives."""
    if k <= 0: return img
    shade = Image.new("RGB", img.size, (20, 24, 48))
    return Image.blend(img, shade, 0.28 * k)


def pill(d, t, x, y, label, col, seed, w=300):
    wrect(d, x, y, x + w, y + 90, t, seed, 7, fill=(255, 252, 242))
    d.rectangle((x + 8, y + 8, x + 26, y + 82), fill=col)
    text(d, label, x + w / 2 + 10, y + 45, 46, col, "mm", "impact.ttf")


def padlock(d, t, cx, cy, s=1.0, col=INK, seed=2000):
    d.arc((cx - 40 * s, cy - 95 * s, cx + 40 * s, cy - 5 * s), 180, 360, fill=col, width=int(12 * s))
    wline(d, [(cx - 40 * s, cy - 50 * s), (cx - 40 * s, cy - 20 * s)], t, seed, int(10 * s), col)
    wline(d, [(cx + 40 * s, cy - 50 * s), (cx + 40 * s, cy - 20 * s)], t, seed + 1, int(10 * s), col)
    wrect(d, cx - 65 * s, cy - 25 * s, cx + 65 * s, cy + 70 * s, t, seed + 2, int(8 * s), fill=MOON)
    d.ellipse((cx - 10 * s, cy + 10 * s, cx + 10 * s, cy + 30 * s), fill=col)


def eye(d, t, cx, cy, crossed, seed):
    d.ellipse((cx - 34, cy - 18, cx + 34, cy + 18), outline=INK, width=5); d.ellipse((cx - 9, cy - 9, cx + 9, cy + 9), fill=INK)
    if crossed: wline(d, [(cx - 40, cy + 28), (cx + 40, cy - 28)], t, seed, 6, RED)


def medal(d, t, cx, cy, k, seed):
    if k <= 0: return
    s = eout(k)
    wline(d, [(cx - 14, cy - 60 * s), (cx, cy - 20 * s)], t, seed, 6, RED); wline(d, [(cx + 14, cy - 60 * s), (cx, cy - 20 * s)], t, seed + 1, 6, NIGHT)
    wcircle(d, cx, cy, 30 * s, t, seed + 2, 5, fill=MOON)
    if k > 0.8: text(d, "★", cx, cy, 30, INK, "mm", "seguisym.ttf")


# ------------------------------------------------------------------ scenes
def sc_intro(img, d, t):
    a, s_ = S("intro")["start"], S("intro")
    sloth(img, t, 640, 980, 620, narr_level(t) or 0.0, "talk", wave=eio(seg(t, a, a + 0.8)) * (1 - seg(t, a + 4.0, a + 4.8)))
    d = ImageDraw.Draw(img)
    z = eout(seg(t, a + 0.3, a + 0.9))
    text(d, "SNOOZY", 1240, 260, int(40 + 110 * z), NIGHT, "mm", "impact.ttf")
    if t > a + 1.8: text(d, "night watchman", 1240, 380, 50, INK)
    if t > a + 4.0: text(d, "officially lazy", 1240, 470, 42, SOFT)
    if t > a + 6.5: stamp(img, "SLOW AND STEADY", 1240, 600, -5, RED, 64)
    return img


def sc_night(img, d, t):
    a0 = S("night")["start"] - 1.2
    moon_window(d, t)
    desk_set(d, t, 1.0)
    scr = Image.open(HERE / "ng" / "world.png").convert("RGB").crop((260, 40, 1260, 690)).resize((306, 206), Image.LANCZOS)
    img.paste(scr, (867, 477)); d = ImageDraw.Draw(img)
    typing = math.sin(t * 30) * 7
    stick(d, t, (720, 800), 1.0, lean=10, armL=(30 + typing, -10), armR=(20 - typing, -20), legL=(170, 100), legR=(160, 95),
          mood="happy", look=0.6, seed=1)
    msgs = [(2.2, "you're SO good at this"), (3.8, "best player I've ever seen"), (5.6, "you're really mature for your age"),
            (7.4, "want free gems? just between us")]
    for i, (t0, s) in enumerate(msgs):
        bubble(d, t, 1220 - i * 20, 150 + i * 150, s, 800 + i * 10, seg(t, a0 + t0, a0 + t0 + 0.35), size=38)
    text(d, "23:04", 345, 520, 48, INK)


CLOCK_AT = 9.6


def sc_stat(img, d, t):
    a = S("stat")["start"]
    k = eio(seg(t, a + 0.8, a + 7.0)); n = int(50000 * k)
    text(d, f"{n:,}" + ("+" if k >= 1 else ""), W / 2, 270, 230, RED, "mm", "impact.ttf")
    text(d, "sextortion reports in 2025", W / 2, 440, 58, INK)
    text(d, "(NCMEC, United States)", W / 2, 505, 36, SOFT)
    pile = int(16 * k)
    for i in range(pile):
        y = 900 - i * 22
        wrect(d, 220 + (i % 2) * 18, y, 480 + (i % 2) * 18, y + 18, t, 900 + i, 4, fill=WHITE)
        if t < a + CLOCK_AT: wrect(d, 1440 - (i % 2) * 18, y, 1700 - (i % 2) * 18, y + 18, t, 950 + i, 4, fill=WHITE)
    if t > a + 8.6:
        k2 = eout(seg(t, a + 8.6, a + 9.0))
        wrect(d, 600, 600, 920, 880, t, 990, 8, fill=(255, 252, 242)); d.rectangle((608, 608, 912, 660), fill=RED)
        text(d, "PER DAY", 760, 634, 40, WHITE, "mm", "impact.ttf")
        text(d, "137", 760, 770, int(60 + 80 * k2), INK, "mm", "impact.ttf")
    if t > a + CLOCK_AT:                                                     # a clock: one every ~10 min
        cx, cy = 1200, 740; wcircle(d, cx, cy, 120, t, 995, 8, fill=(255, 252, 242))
        ang = -math.pi / 2 + (t - a - CLOCK_AT) * 2.2
        wline(d, [(cx, cy), (cx + 95 * math.cos(ang), cy + 95 * math.sin(ang))], t, 996, 7, RED)
        wline(d, [(cx, cy), (cx, cy - 60)], t, 997, 9)
        text(d, "1 every", 1420, 710, 44, INK, "lm"); text(d, "~10 min", 1420, 775, 60, RED, "lm", "impact.ttf")


def sc_fast(img, d, t):
    a = S("fast")["start"]
    cx, cy = W / 2, 470
    wcircle(d, cx, cy, 260, t, 1100, 10, fill=(255, 252, 242))
    wrect(d, cx - 40, cy - 310, cx + 40, cy - 270, t, 1101, 8, fill=INK)
    k = eio(seg(t, a + 0.5, a + 5.5))
    for i in range(12):
        an = i / 12 * 2 * math.pi - math.pi / 2
        wline(d, [(cx + 220 * math.cos(an), cy + 220 * math.sin(an)), (cx + 245 * math.cos(an), cy + 245 * math.sin(an))], t, 1110 + i, 5)
    pts = [(cx, cy)] + [(cx + 200 * math.cos(-math.pi / 2 + j / 30 * k * 2 * math.pi * 0.3),
                         cy + 200 * math.sin(-math.pi / 2 + j / 30 * k * 2 * math.pi * 0.3)) for j in range(31)]
    if k > 0.02: d.polygon(pts, fill=(255, 190, 190))
    an = -math.pi / 2 + k * 2 * math.pi * 0.3
    wline(d, [(cx, cy), (cx + 210 * math.cos(an), cy + 210 * math.sin(an))], t, 1150, 9, RED)
    text(d, f"{int(18 * k)} min", cx, cy + 90, 80, INK, "mm", "impact.ttf")
    text(d, "first contact to first sexual request", W / 2, 830, 54, INK)
    text(d, "18 minutes to 82 hours (Swansea University, 2016)", W / 2, 900, 34, SOFT)


def sc_platforms(img, d, t):
    a = S("platforms")["start"]
    apps = [("Roblox", RED), ("Discord", (88, 101, 242)), ("Minecraft", GREEN), ("TikTok", INK)]
    for i, (n, col) in enumerate(apps):
        t0 = a + 0.4 + i * 0.7
        if t < t0: continue
        x, y = 120 + (i % 2) * 520, 120 + (i // 2) * 300
        pill(d, t, x, y, n, col, 1200 + i * 10, 360)
        for j in range(7):                                                   # its own little fence
            fx = x - 10 + j * 64
            wline(d, [(fx, y + 150), (fx, y + 200)], t, 1250 + i * 10 + j, 5, SOFT)
        wline(d, [(x - 20, y + 165), (x + 390, y + 165)], t, 1290 + i, 5, SOFT)
        eye(d, t, x + 410, y + 45, False, 1300 + i)
    if t > a + 4.6: text(d, "each one only watches its own backyard", 560, 760, 46, INK)
    if t > a + 8.6:                                                          # the jump to an encrypted app
        k = eout(seg(t, a + 8.6, a + 9.8))
        sx, sy, ex, ey = 520, 220, 1420, 420
        mx = sx + (ex - sx) * k; my = sy + (ey - sy) * k - 180 * math.sin(math.pi * k)
        pts = [(sx + (mx - sx) * j / 12, sy + (my - sy) * j / 12 - 180 * math.sin(math.pi * k * j / 12) * (1 - j / 12)) for j in range(13)]
        wline(d, pts, t, 1350, 8, RED)
        padlock(d, t, 1500, 420, 1.6)
        text(d, "encrypted app", 1500, 620, 50, INK)
        if t > a + 11.2:
            eye(d, t, 1500, 710, True, 1360)
            text(d, "no one else sees", 1500, 790, 50, RED)


def sc_parents(img, d, t):
    a = S("parents")["start"]
    r = random.Random(12)
    for i in range(40):
        x = r.uniform(60, 1000); sp = r.uniform(250, 420); y = -80 + (t - a - r.uniform(0, 2.4)) * sp
        if -80 < y < 900:
            wrect(d, x, y, x + 150, y + 56, t, 1000 + i, 4, fill=WHITE)
            wline(d, [(x + 18, y + 22), (x + 130, y + 22)], t, 1100 + i, 4, SOFT); wline(d, [(x + 18, y + 38), (x + 90, y + 38)], t, 1200 + i, 4, SOFT)
    stick(d, t, (520, 780), 1.15, lean=-6, armL=(150, 200), armR=(30, -60), legL=(105, 90), legR=(75, 90), mood="sad", look=-0.4, seed=40)
    text(d, "?", 640, 330 + math.sin(t * 6) * 8, 120, RED, "mm", "impact.ttf")
    stick(d, t, (1450, 820), 0.85, armL=(200, 240), armR=(-40, -80), legL=(105, 90), legR=(75, 90), mood="happy", look=-0.6, seed=60)
    bubble(d, t, 1210, 330, "free gift for you!", 1300, seg(t, a + 2.6, a + 3.0), size=38)
    if t > a + 4.0:
        hx, hy = 1520, 470
        wline(d, [(hx, 430), (hx, hy + 30)], t, 1310, 5)
        d.arc((hx - 34, hy, hx + 6, hy + 60), 0, 200, fill=RED, width=7)
        text(d, "the trap", hx + 130, hy + 40, 38, RED)


def sc_guard(img, d, t):
    a = S("guard")["start"]
    k = seg(t, a + 0.2, a + 1.4)
    shield(d, t, 520, 380, 1.2, k if k < 1 else 1.0)
    poof(d, t, 520, 380, seg(t, a + 1.3, a + 2.0))
    if t > a + 1.4:
        z = eout(seg(t, a + 1.4, a + 1.9))
        text(d, "NIGHT GUARD", 520, 650, int(40 + 70 * z), NIGHT, "mm", "impact.ttf")
    if t > a + 3.0:                                                          # the family's own computer
        x, y = 900, 160
        wrect(d, x, y, x + 300, y + 180, t, 1400, 7, fill=(225, 238, 255))
        wline(d, [(x - 30, y + 200), (x + 330, y + 200)], t, 1401, 8)
        wline(d, [(x + 90, y + 130), (x + 150, y + 60), (x + 210, y + 130)], t, 1402, 6)
        wrect(d, x + 115, y + 105, x + 185, y + 150, t, 1403, 5)
        text(d, "runs on the family's", x + 360, y + 70, 40, INK, "lm"); text(d, "own computer", x + 360, y + 125, 40, INK, "lm")
    if t > a + 6.0:                                                          # reads the screen -> covers encrypted apps
        padlock(d, t, 1130, 600, 1.1)
        shield(d, t, 1250, 600, 0.45, 1.0, seed=560)
        text(d, "reads the screen, so it protects", 1320, 570, 33, INK, "lm")
        text(d, "even inside encrypted apps", 1320, 625, 33, GREEN, "lm")
    if t > a + 9.5:
        text(d, "the chat never leaves home", 1340, 735, 44, NIGHT, "lm", "impact.ttf")


def popup(d, t, x, y, k):  # noqa: C901
    """The child's warning, redrawn in the app's colors (Portuguese text from guard/signals.py)."""
    if k <= 0: return
    w, h = 720, 640; yy = y + (1 - eout(k)) * 80
    d.rounded_rectangle((x, yy, x + w, yy + h), 26, fill=PANEL, outline=(255, 122, 138), width=6)
    text(d, "🛑", x + 40, yy + 52, 40, RED, "mm", "seguiemj.ttf")
    text(d, "Stop! This could be dangerous", x + 80, yy + 52, 42, WHITE, "lm", "segoeuib.ttf")
    kid = SIGNALS["secrecy"]["kid"]["en"]
    for i, ln in enumerate(textwrap.wrap(kid, 40)[:6]):
        text(d, ln, x + 36, yy + 120 + i * 44, 32, WHITE, "lm", "segoeui.ttf")
    text(d, '"don\'t tell your parents ok? they wouldn\'t get it"', x + 36, yy + 400, 26, (166, 174, 214), "lm", "segoeuii.ttf")
    fam_on = FAMILY_AT <= t < FAMILY_AT + _mp3_dur(FAMILY_FILE) and int(t * 3) % 2 == 0
    d.rounded_rectangle((x + 30, yy + 440, x + w - 30, yy + 510), 14, fill=(70, 62, 30) if fam_on else (42, 47, 94),
                        outline=MOON, width=6 if fam_on else 2)
    text(d, "Your family will know. You're not in trouble.", x + 50, yy + 475, 25, WHITE, "lm", "segoeui.ttf")
    d.rounded_rectangle((x + 30, yy + 545, x + 200, yy + 610), 12, fill=MOON)
    text(d, "Got it", x + 115, yy + 577, 32, (42, 32, 0), "mm", "segoeuib.ttf")
    d.rounded_rectangle((x + 220, yy + 545, x + 520, yy + 610), 12, outline=(80, 90, 150), width=3)
    text(d, "Tell someone", x + 370, yy + 577, 30, WHITE, "mm", "segoeuib.ttf")


def game_chat(d, t, a):
    x, y = 90, 140
    img = d._image
    w = Image.open(HERE / "ng" / "world.png").convert("RGB")
    w = w.crop((180, 0, 180 + 1140, 720)).resize((760, 480), Image.LANCZOS)          # castle, both avatars and the sky
    mask = Image.new("L", w.size, 0); ImageDraw.Draw(mask).rounded_rectangle((0, 0, 759, 479), 24, fill=255)
    img.paste(w, (x, y), mask)
    d.rounded_rectangle((x, y + 490, x + 760, y + 760), 24, fill=(28, 70, 50))
    msgs = [("Alex_17", "how old r u? parents home?"), ("you", "11. they're at work"),
            ("Alex_17", "don't tell your parents ok?")]
    for i, (who, s) in enumerate(msgs):
        if t > a + 0.6 + i * 1.6:
            text(d, f"{who}: {s}", x + 30, y + 545 + i * 66, 28, WHITE if who != "you" else MOON, "lm", "segoeui.ttf")


def sc_alert(img, d, t):
    a = S("alert")["start"]
    game_chat(d, t, a)
    popup(d, t, 1060, 150, seg(t, SARAH_AT - 0.8, SARAH_AT - 0.3))
    if t >= SARAH_AT - 0.3:
        speaker(d, t, 930, 470, max(level(SARAH_FILE, SARAH_AT, t), level(FAMILY_FILE, FAMILY_AT, t)))
        stamp(img, "DANGER", 1420, 880, 6, RED, 74)
    return img


def sc_family(img, d, t):
    a = S("family")["start"]
    stick(d, t, (330, 800), 1.15, armL=(110, -60), armR=(60, -100), legL=(105, 90), legR=(75, 90),
          mood="happy" if t > a + 3 else "normal", look=0.6, seed=110)
    shield(d, t, 330, 250, 0.55, 1.0, seed=580)
    text(d, "the Night Guard", 330, 400, 46, NIGHT, "mm", "impact.ttf")
    phone(d, t, 640, 120, seg(t, a + 2.0, a + 2.4), ["HIGH risk · Roblox", "secret, photo request"])
    steps = [(a + 4.4, "talk calmly"), (a + 5.4, "keep screenshots"), (a + 6.4, "block and report")]
    text(d, "what to do now", 670, 440, 40, NIGHT, "lm", "impact.ttf")
    for i, (t0, s) in enumerate(steps):
        if t > t0 - 0.3: check(d, t, 670, 520 + i * 80, seg(t, t0, t0 + 0.3), s, 1500 + i * 10)
    if t > a + 4.0:
        text(d, "one alert", 1500, 300, 60, RED, "mm", "impact.ttf")
        text(d, "not the whole chat", 1500, 380, 44, INK)
        text(d, "NCMEC CyberTipline · SaferNet", 1500, 470, 32, SOFT)


def card_tiny(d, t, x, y, k, title, l1, l2, col, seed):
    if k <= 0: return
    s = eout(k); w, h = 350 * s, 300 * s; cx, cy = x + 175, y + 150
    wrect(d, cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2, t, seed, 6, fill=(255, 252, 242))
    if k > 0.7:
        d.rectangle((cx - w / 2 + 7, cy - h / 2 + 7, cx + w / 2 - 7, cy - h / 2 + 20), fill=col)
        text(d, title, cx, cy - 62, 50, col, "mm", "impact.ttf")
        text(d, l1, cx, cy + 20, 26, INK); text(d, l2, cx, cy + 72, 26, SOFT)


def card_small(d, t, x, y, k, title, l1, l2, col, seed):
    if k <= 0: return
    s = eout(k); w, h = 560 * s, 330 * s; cx, cy = x + 280, y + 165
    wrect(d, cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2, t, seed, 7, fill=(255, 252, 242))
    if k > 0.7:
        d.rectangle((cx - w / 2 + 8, cy - h / 2 + 8, cx + w / 2 - 8, cy - h / 2 + 22), fill=col)
        text(d, title, cx, cy - 70, 66, col, "mm", "impact.ttf")
        text(d, l1, cx, cy + 20, 38, INK); text(d, l2, cx, cy + 80, 34, SOFT)


def sc_peace(img, d, t):
    a = S("peace")["start"]
    # left: the kid sleeping safe, whole body under the blanket
    kid_in_bed(d, t)
    for i in range(3):
        zt = (t * 0.7 + i * 0.33) % 1
        text(d, "z", 360 + zt * 80, 520 - zt * 140, int(36 + 26 * zt), NIGHT, "mm", "impact.ttf")
    text(d, "peace for the kid", 450, 960 - 40, 50, NIGHT)
    # right: parents relaxed on the sofa
    if t > a + 2.0:
        wrect(d, 1100, 700, 1760, 820, t, 1950, 8, fill=(240, 200, 170))
        wrect(d, 1100, 600, 1760, 700, t, 1951, 8, fill=(250, 215, 185))
        stick(d, t, (1320, 700), 0.85, armL=(160, 200), armR=(30, -40), legL=(20, 90), legR=(10, 90), mood="happy", seed=130)
        stick(d, t, (1540, 700), 0.85, armL=(150, 170), armR=(20, -60), legL=(20, 90), legR=(10, 90), mood="happy", seed=140)
        for i in range(3):
            ht = (t * 0.6 + i * 0.33) % 1
            text(d, "♥", 1430 + (i - 1) * 60, 380 - ht * 120, int(40 + 20 * ht), RED, "mm", "seguisym.ttf")
        text(d, "peace for parents", 1430, 920, 50, NIGHT)
    if t > a + 5.0:
        shield(d, t, W / 2, 330, 0.55, 1.0, "sleep", seed=600)
        text(d, "the guard rests", W / 2, 470, 38, INK)


# ------------------------------------------------------------------ new scenes: the Switch family room
SWITCH_COL = (67, 56, 202)
SHOTS = HERE / "ng" / "shots"                       # real screenshots of Mattermost on a real Switch run


def say(sid, kw):
    """When the narrator says `kw` in scene `sid` (so things appear on the word)."""
    s = S(sid); i = s["line"].find(kw)
    return s["start"] + s["voice_dur"] * max(0, i) / len(s["line"])


@lru_cache(maxsize=16)
def shot(name, width):
    im = Image.open(SHOTS / f"{name}.png").convert("RGB")
    return im.resize((width, int(im.height * width / im.width)), Image.LANCZOS)


def taped(img, t, name, cx, cy, width, rot=-2.0, k=1.0):
    """A real screenshot taped on the paper (same look as the Night Guard film)."""
    if k <= 0: return
    sh = shot(name, int(width))
    card = Image.new("RGBA", (sh.width + 28, sh.height + 28), (255, 255, 255, 255))
    card.paste(sh, (14, 14))
    ang = rot + (1 - eout(k)) * 8
    card = card.rotate(ang, expand=True, resample=Image.BICUBIC)
    shadow = Image.new("RGBA", card.size, (0, 0, 0, 0)); shadow.putalpha(card.split()[3].point(lambda v: v * 0.25))
    y = cy - card.height / 2 + (1 - eout(k)) * 120
    img.paste(Image.new("RGB", card.size, (90, 80, 70)), (int(cx - card.width / 2 + 12), int(y + 14)), shadow)
    img.paste(card, (int(cx - card.width / 2), int(y)), card)
    a = random.Random(9)
    for dx, tr in ((-0.42, -18), (0.4, 14)):
        tape = Image.new("RGBA", (170, 50), (255, 236, 150, 170)).rotate(tr + a.uniform(-3, 3), expand=True)
        img.paste(tape, (int(cx + dx * card.width - tape.width / 2), int(y + 6 - tape.height / 2)), tape)


def big(d, t, x, y, value, label, t0, col=NIGHT, size=150, sub=None):
    """A big number that pops on the word, with its label (and source) under it."""
    if t < t0: return
    z = eout(seg(t, t0, t0 + 0.4))
    text(d, value, x, y, int(size * (0.4 + 0.6 * z)), col, "mm", "impact.ttf")
    text(d, label, x, y + size * 0.62, 40, INK)
    if sub: text(d, sub, x, y + size * 0.62 + 46, 28, SOFT)


def sc_hello(img, d, t):
    a = S("hello")["start"]
    z = eout(seg(t, a + 0.2, a + 0.8))
    text(d, "Jennifer Evangelista", W / 2, 230, int(40 + 80 * z), NIGHT, "mm", "impact.ttf")
    if t > a + 1.6: text(d, "data engineering · solutions architecture", W / 2, 350, 50, INK)
    if t > a + 2.6: text(d, "Florianópolis, Brazil", W / 2, 420, 44, SOFT)
    if t > say("hello", "Night Guard"):
        shield(d, t, 470, 700, 0.75, 1.0, seed=640)
        text(d, "NIGHT GUARD", 470, 900, 50, NIGHT, "mm", "impact.ttf")
    if t > say("hello", "Best Use"): stamp(img, "WINNER · BEST USE OF BACKBOARD", 1180, 640, -4, RED, 58)
    if t > say("hello", "Flip the Switch"): stamp(img, "FLIP THE SWITCH · TRACK 02", 1180, 820, 3, SWITCH_COL, 58)
    sloth(img, t, 1700, 1000, 400, narr_level(t) or 0.0, "talk", wave=eio(seg(t, a, a + 0.8)) * (1 - seg(t, a + 3.0, a + 3.8)))
    return img


def sc_guard2(img, d, t):
    a = S("guard")["start"]
    k = seg(t, a + 0.2, a + 1.4)
    shield(d, t, 480, 400, 1.2, k if k < 1 else 1.0)
    poof(d, t, 480, 400, seg(t, a + 1.3, a + 2.0))
    if t > a + 1.4:
        z = eout(seg(t, a + 1.4, a + 1.9))
        text(d, "NIGHT GUARD", 480, 670, int(40 + 70 * z), NIGHT, "mm", "impact.ttf")
    if t > say("guard", "kid's computer"):
        x, y = 900, 200
        wrect(d, x, y, x + 300, y + 180, t, 1400, 7, fill=(225, 238, 255))
        wline(d, [(x - 30, y + 200), (x + 330, y + 200)], t, 1401, 8)
        text(d, "on the kid's", x + 360, y + 70, 44, INK, "lm"); text(d, "own computer", x + 360, y + 125, 44, INK, "lm")
    if t > say("guard", "Gemma"): stamp(img, "GEMMA · OPEN MODEL", 1240, 560, -3, NIGHT, 60)
    if t > say("guard", "never leaves"): text(d, "the chat never leaves home", 1240, 760, 56, GREEN, "mm", "impact.ttf")


def sc_results(img, d, t):
    big(d, t, 480, 250, "36/36", "risky chats caught", say("results", "thirty six out"), RED)
    big(d, t, 1440, 250, "3/34", "false alarms on safe chats", say("results", "three false"), NIGHT)
    big(d, t, 480, 650, "~3.4 s", "per check, on the computer", say("results", "three and a half"), NIGHT)
    big(d, t, 1440, 650, "14", "grooming tactics it knows", say("results", "fourteen"), RED)
    text(d, "Night Guard evaluation · 70 fictional chats · Gemma 4 E4B, local", W / 2, 950, 32, SOFT)


def sc_before(img, d, t):
    a = S("before")["start"]
    stamp(img, "BEFORE", 300, 150, -6, RED, 90)
    moon_window(d, t, 120, 260, 420, 540)
    stick(d, t, (760, 840), 1.15, lean=-4, armL=(110, -70), armR=(70, -110), legL=(105, 90), legR=(75, 90),
          mood="sad", look=0.5, seed=210)
    phone(d, t, 820, 200, seg(t, say("before", "one alert"), say("before", "one alert") + 0.4),
          ["HIGH risk · Roblox", "asked to keep a secret"])
    text(d, "23:07", 1060, 960, 46, INK)
    qs = [("What does it mean?", "mean"), ("What do I say?", "say"), ("Where do I report it?", "report")]
    for i, (q, kw) in enumerate(qs):
        t0 = say("before", kw)
        if t > t0 - 0.2:
            text(d, "?", 1360, 300 + i * 170, int(60 + 50 * eout(seg(t, t0 - 0.2, t0 + 0.2))), RED, "mm", "impact.ttf")
            text(d, q, 1410, 300 + i * 170, 42, INK, "lm")
    if t > say("before", "alone"): text(d, "alone", 1650, 840, 64, RED, "mm", "impact.ttf")
    return dark_overlay(img, 0.6)


def sc_room(img, d, t):
    stamp(img, "AFTER · WITH SWITCH", 380, 130, -5, GREEN, 72)
    wrect(d, 90, 380, 400, 580, t, 3200, 7, fill=(225, 238, 255))              # the kid's computer
    shield(d, t, 245, 480, 0.35, 1.0, seed=660)
    text(d, "the kid's computer", 245, 640, 36, INK)
    k = eout(seg(t, say("room", "Switch") - 0.2, say("room", "Switch") + 0.3))
    if k > 0:
        wrect(d, 560 - 130 * k, 410, 560 + 130 * k, 550, t, 3210, 8, fill=SWITCH_COL)
        if k > 0.7: text(d, "SWITCH", 560, 480, 60, WHITE, "mm", "impact.ttf")
    taped(img, t, "alert", 1330, 470, 1060, -1.5, seg(t, say("room", "group chat"), say("room", "group chat") + 0.5))
    if t > say("room", "Never"):
        stamp(img, "ONLY THE FLAGGED PHRASE", 1270, 900, 3, RED, 56)


def sc_helper(img, d, t):
    taped(img, t, "plan", 640, 500, 1100, 2.0, seg(t, S("helper")["start"] + 0.2, S("helper")["start"] + 0.7))
    if t > say("helper", "second and a half"): big(ImageDraw.Draw(img), t, 1520, 300, "~1.5 s", "alert to plan",
                                                   say("helper", "second and a half"), SWITCH_COL, 130, "fixed texts")
    if t > say("helper", "waits"): stamp(img, "WAITING FOR A PARENT", 1500, 720, -5, RED, 56)
    if t > say("helper", "Only"): text(ImageDraw.Draw(img), "only mom or dad decide", 1500, 880, 44, NIGHT, "mm", "impact.ttf")


def sc_decide(img, d, t):
    a = S("decide")["start"]
    taped(img, t, "approve", 520, 430, 760, -2.5, seg(t, a, a + 0.5))
    taped(img, t, "talk", 1360, 560, 900, 2.0, seg(t, say("decide", "Dad"), say("decide", "Dad") + 0.5))
    if t > say("decide", "document"): stamp(img, "SAVED IN THE ROOM", 560, 930, -4, GREEN, 56)


def sc_kid(img, d, t):
    a = S("kid")["start"]
    taped(img, t, "lia", 1180, 500, 1100, -1.5, seg(t, a + 0.2, a + 0.7))
    stick(d, t, (260, 860), 1.0, lean=4, armL=(60, -40), armR=(40, -60), legL=(105, 90), legR=(75, 90),
          mood="happy" if t > say("kid", "not in trouble") else "normal", look=0.6, seed=260)
    text(d, "Lia", 260, 520, 44, NIGHT, "mm", "impact.ttf")
    if t > say("kid", "not in trouble"): stamp(img, "YOU'RE NOT IN TROUBLE", 1180, 960, 3, GREEN, 60)


def sc_threat(img, d, t):
    a = S("threat")["start"]
    taped(img, t, "threat", 560, 500, 1000, -2.0, seg(t, a + 0.2, a + 0.7))
    t1 = say("threat", "SaferNet")
    for i, (n, sub) in enumerate([("SAFERNET", "Brasil"), ("NCMEC", "CyberTipline")]):
        if t > t1 + i * 0.5:
            x = 1180 + i * 360
            wrect(d, x, 200, x + 320, 380, t, 3610 + i, 7, fill=(255, 252, 242))
            text(d, n, x + 160, 265, 54, NIGHT, "mm", "impact.ttf"); text(d, sub, x + 160, 335, 32, SOFT)
    if t > say("threat", "don't pay"): stamp(img, "DON'T PAY", 1520, 560, -6, RED, 110)
    if t > say("threat", "fixed"): text(d, "fixed text · never improvised", 1520, 760, 44, INK)


def sc_beforeafter(img, d, t):
    a = S("beforeafter")["start"]
    d.line([(W / 2, 120), (W / 2, 900)], fill=INK, width=6)
    stamp(img, "BEFORE", W / 4, 160, -4, RED, 80)
    if t > say("beforeafter", "After"): stamp(img, "AFTER", 3 * W / 4, 160, 4, GREEN, 80)
    before = [("one scary alert", "one scary"), ("a parent alone", "alone"), ("no plan", "no plan")]
    after = [("the whole family", "whole family"), ("a clear plan", "clear plan"), ("the kid in the loop", "kid in")]
    for i, (s, kw) in enumerate(before):
        t0 = say("beforeafter", kw)
        if t > t0:
            y = 360 + i * 170
            wline(d, [(160, y - 20), (200, y + 20)], t, 3800 + i, 8, RED); wline(d, [(160, y + 20), (200, y - 20)], t, 3810 + i, 8, RED)
            text(d, s, 240, y, 52, INK, "lm")
    for i, (s, kw) in enumerate(after):
        t0 = say("beforeafter", kw)
        if t > t0 - 0.2:
            y = 360 + i * 170
            check(d, t, 1060, y, seg(t, t0 - 0.2, t0 + 0.1), "", 3820 + i)
            text(d, s, 1140, y, 52, INK, "lm")


def sc_proof(img, d, t):
    big(d, t, 480, 230, "13", "end-to-end checks on a real Switch", say("proof", "thirteen"), RED, 170, "every push · GitHub Actions")
    big(d, t, 1440, 230, "2 + 2", "agents and linked rooms", say("proof", "two agents"), SWITCH_COL, 170)
    big(d, t, W / 2, 620, "0", "lines of the private chat reach the parents", say("proof", "Zero"), GREEN, 220,
        "checked on every run · 17 unit tests too")


def sc_end(img, d, t):
    a = S("end")["start"]
    sloth(img, t, 1720, 990, 340, narr_level(t) or 0.0, "talk", wave=eio(seg(t, a + 3.0, a + 3.6)))
    d = ImageDraw.Draw(img)
    shield(d, t, W / 2, 230, 0.8, 1.0)
    z = eout(seg(t, a, a + 0.5))
    text(d, "Night Guard Family Room", W / 2, 480, int(50 + 60 * z), NIGHT, "mm", "impact.ttf")
    if t > a + 1.0: text(d, "a partner for parents · a friend for kids · a plan for the whole family", W / 2, 600, 44, INK)
    if t > a + 2.4: text(d, "github.com/jenniferevangelista-de/night-guard-switch", W / 2, 700, 46, RED)
    if t > a + 3.0: text(d, "Jennifer Evangelista · Switch · Mattermost · Gemma · Night Guard", W / 2, 790, 34, SOFT)
    text(d, 'Music: "Funkorama" Kevin MacLeod (incompetech.com), CC BY 4.0 · opening score: original', W / 2, 1050, 22, SOFT)


ORDER = [("hello", sc_hello), ("night", sc_night), ("stat", sc_stat), ("fast", sc_fast), ("guard", sc_guard2),
         ("results", sc_results), ("alert", sc_alert), ("before", sc_before), ("room", sc_room), ("helper", sc_helper),
         ("decide", sc_decide), ("kid", sc_kid), ("threat", sc_threat), ("beforeafter", sc_beforeafter),
         ("proof", sc_proof), ("end", sc_end)]


def render(t):
    img = paper().copy(); d = ImageDraw.Draw(img)
    fn = ORDER[0][1]
    for sid, f in ORDER:
        if t >= (S(sid)["start"] if sid != "hello" else 0): fn = f
    img = fn(img, d, t) or img
    img = dark_overlay(img, seg(t, S("night")["start"] - 0.8, S("night")["start"]) * (1 - seg(t, MUSIC_SWITCH, MUSIC_SWITCH + 1.5)))
    if fn not in (sc_hello, sc_end):                     # Snoozy, Night Guard's little guard, in the corner
        m = narr_level(t)
        sloth(img, t, 1825, 1010, 200, m or 0.0, "talk" if m is not None else "listen",
              emo="angry" if S("night")["start"] <= t < MUSIC_SWITCH else "happy")
    if fn is not sc_end: subtitle(ImageDraw.Draw(img), t)
    if t < 1.0: img = Image.blend(Image.new("RGB", img.size, (0, 0, 0)), img, t)    # fade in from black
    return img


if __name__ == "__main__":
    rv = WORK / "review"; rv.mkdir(parents=True, exist_ok=True)
    pts = [float(a) for a in sys.argv[1:]] or [3, 9, 30, 60]
    for x in pts:
        render(x).save(rv / f"f_{x:05.1f}.jpg", quality=82)
    print("ok", DUR, "sarah at", SARAH_AT, "switch", MUSIC_SWITCH)
