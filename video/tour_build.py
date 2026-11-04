"""Build the tour: the real Switch + Mattermost recording in a frame on paper, Snoozy narrating beside it,
part titles and subtitles. PRE-EXISTING design and most of the code: the Night Guard tour builder
(video/walkthrough/wt_build.py in github.com/jenniferevangelista-de/night-guard). New: the waits for the agent
(Gemma writing on a CPU) are cut out, and Jennifer's opening line.

  python video/tour_build.py      -> video/out/night_guard_family_room_tour.mp4
Needs video/work/ from the recording job: raw/*.webm, scenes.json, voice/, tour_narration.json.
"""
import json
import subprocess
import sys
import textwrap
from functools import lru_cache
from pathlib import Path

import numpy as np
import soundfile as sf
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
WORK, OUT = HERE / "work", HERE / "out"
sys.path.insert(0, str(HERE / "ng"))
from palito import INK, font, paper, text  # noqa: E402
from ng_sloth import sloth  # noqa: E402

W, H, FPS, SR = 1920, 1080, 24, 48000
FX, FY, FW, FH = 40, 108, 1536, 864                    # where the recording sits (16:9)
NIGHT = (38, 50, 108); SOFT = (120, 112, 125)

narr = {n["id"]: n for n in json.loads((WORK / "tour_narration.json").read_text(encoding="utf-8"))}
scenes = json.loads((WORK / "scenes.json").read_text())
raw = sorted((WORK / "raw").glob("*.webm"))[0]


def _dur(p):
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(p)],
                                capture_output=True, text=True).stdout)


# Keep the recording from the first scene to the last; cut the waits for the agent, keeping a beat on each side.
begin = max(0.0, scenes[0]["start"] - 0.2)
end_t = min(_dur(raw), scenes[-1]["end"] + 0.3)
gaps = [(s["start"] + 1.5, s["at"] - 0.8) for s in scenes if s["at"] - s["start"] > 4]
keep, t = [], begin
for g0, g1 in gaps:
    keep.append((t, g0)); t = g1
keep.append((t, end_t))


def new_time(x):
    return sum(max(0.0, min(x, b) - a) for a, b in keep)


segs = [{"id": s["key"], "vstart": round(new_time(s["at"]), 2)} for s in scenes]
rec = WORK / "tour_cut.mp4"
select = "+".join(f"between(t,{a:.3f},{b:.3f})" for a, b in keep)
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(raw), "-vf",
                f"fps={FPS},select='{select}',setpts=N/{FPS}/TB,scale={FW}:{FH}:flags=lanczos", "-an",
                "-c:v", "libx264", "-crf", "17", "-pix_fmt", "yuv420p", str(rec)], check=True)
DUR = round(segs[-1]["vstart"] + narr[segs[-1]["id"]]["dur"] + 2.0, 2)   # the last screen holds until Snoozy is done
print("recording cut to", round(_dur(rec), 1), "s; video", DUR, "s")


def load(p):
    tmp = WORK / "_tmp.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(p), "-ac", "1", "-ar", str(SR), str(tmp)], check=True)
    a, _ = sf.read(tmp, dtype="float64"); tmp.unlink(); return a


@lru_cache(maxsize=32)
def env(path):
    a = load(path); hop = SR // 12
    r = np.array([np.sqrt(np.mean(a[j:j + hop] ** 2)) for j in range(0, len(a), hop)])
    return (r / (r.max() or 1)).tolist()


def talking(t):
    """Snoozy's mouth follows the narration loudness (closed in the pauses)."""
    for s in segs:
        n = narr[s["id"]]
        if s["vstart"] <= t < s["vstart"] + n["dur"]:
            if n["who"] != "snoozy":
                return None            # Jennifer is speaking: Snoozy listens
            e = env(str(WORK / n["voice"])); k = int((t - s["vstart"]) * 12)
            m = e[k] if 0 <= k < len(e) else 0.0
            return 0.0 if m < 0.12 else min(1.0, m * 1.25)
    return None


def subs():
    out = []
    for s in segs:
        n = narr[s["id"]]
        parts = [p.strip() for p in n["line"].replace(": ", ":|").replace(". ", ".|").replace("? ", "?|").split("|") if p.strip()]
        total = sum(len(p) for p in parts); t = s["vstart"]
        for p in parts:
            d = n["dur"] * len(p) / total; out.append((t, t + d + 0.15, p, s["id"])); t += d
    return out


SUBS = subs()


@lru_cache(maxsize=1)
def base():
    """Paper with a transparent window where the recording shows through, plus a soft shadow and frame."""
    im = paper().copy().convert("RGBA")
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(sh)
    d.rounded_rectangle((FX + 10, FY + 14, FX + FW + 10, FY + FH + 14), 22, fill=(60, 50, 40, 70))
    im = Image.alpha_composite(im, sh)
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((FX - 8, FY - 8, FX + FW + 8, FY + FH + 8), 26, fill=(34, 30, 38, 255))
    hole = Image.new("L", (W, H), 255); ImageDraw.Draw(hole).rounded_rectangle((FX, FY, FX + FW, FY + FH), 18, fill=0)
    im.putalpha(Image.fromarray(np.minimum(np.array(im.split()[3]), np.array(hole))))
    text(ImageDraw.Draw(im), "Night Guard Family Room · a real run on Switch + Mattermost · every chat is fictional",
         FX + FW / 2, FY - 52, 34, SOFT)
    return im


def frame(t):
    im = base().copy(); d = ImageDraw.Draw(im)
    cur = [s for s in segs if s["vstart"] <= t]
    sid = cur[-1]["id"] if cur else segs[0]["id"]
    idx = [s["id"] for s in segs].index(sid) + 1
    cx = (FX + FW + W) / 2
    text(d, f"{idx}/{len(segs)}", cx, 150, 40, SOFT)
    for i, ln in enumerate(textwrap.wrap(narr[sid]["title"], 11)):
        text(d, ln, cx, 220 + i * 66, 60, NIGHT, "mm", "impact.ttf")
    m = talking(t)                               # Snoozy, Night Guard's little guard, beside the run
    sloth(im, t, cx, 1000, 330, m or 0.0, "talk" if m is not None else "listen")
    d = ImageDraw.Draw(im)
    for a, b, s, _ in SUBS:
        if a <= t < b:
            f = font("segoeprb.ttf", 38)
            lines = textwrap.wrap(s, 70) if d.textlength(s, font=f) > 1500 else [s]
            hh = 54 * len(lines); y0 = FY + FH - 30 - hh
            mw = max(d.textlength(ln, font=f) for ln in lines)
            d.rounded_rectangle((FX + FW / 2 - mw / 2 - 22, y0 - 8, FX + FW / 2 + mw / 2 + 22, y0 + hh + 4), 16,
                                fill=(255, 251, 240, 235))
            for i, ln in enumerate(lines):
                text(d, ln, FX + FW / 2, y0 + 25 + i * 54, 38, INK)
            break
    return im


def mix():
    N = int(DUR * SR); voice = np.zeros(N)

    def add(buf, t0, a, g=0.9):
        i = int(t0 * SR)
        if i >= N: return
        j = min(N, i + len(a)); buf[i:j] += a[: j - i] * g
    for s in segs:
        a = load(WORK / narr[s["id"]]["voice"]); add(voice, s["vstart"], a / (np.abs(a).max() + 1e-9))
    music = load(HERE / "ng" / "music" / "Funkorama.mp3")
    while len(music) < N: music = np.concatenate([music, music])
    music = music[:N] / (np.abs(music).max() + 1e-9)
    kern = SR // 4; c = np.cumsum(np.concatenate([np.zeros(kern), (np.abs(voice) > 0.02).astype(float)]))
    duck = 1 - 0.65 * np.clip((c[kern:] - c[:-kern]) / kern * 3, 0, 1)
    fade = np.ones(N); fade[int((DUR - 2) * SR):] = np.linspace(1, 0, N - int((DUR - 2) * SR))
    out = voice + music * 0.30 * duck * fade   # Funkorama at 30%, ducked under the voice
    out = np.tanh(out * 0.9) / np.tanh(0.9); out = out / np.abs(out).max() * 0.95
    sf.write(WORK / "_tour_mix.wav", np.stack([out, out], 1), SR)


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    mix()
    dst = OUT / "night_guard_family_room_tour.mp4"
    ff = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-i", str(rec),
                           "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                           "-i", str(WORK / "_tour_mix.wav"),
                           "-filter_complex", f"[0:v]fps={FPS},tpad=stop_mode=clone:stop_duration=6,pad={W}:{H}:{FX}:{FY}:color=#f7f2e6[bg];[bg][1:v]overlay=0:0:shortest=1[v]",
                           "-map", "[v]", "-map", "2:a", "-t", str(DUR), "-c:v", "libx264", "-preset", "medium", "-crf", "19",
                           "-pix_fmt", "yuv420p", "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-c:a", "aac", "-ar", "48000", "-b:a", "192k", str(dst)],
                          stdin=subprocess.PIPE)
    for i in range(int(DUR * FPS)):
        ff.stdin.write(frame(i / FPS).tobytes())
    ff.stdin.close(); ff.wait()
    (WORK / "_tour_mix.wav").unlink()
    print("done", dst.name, DUR)
