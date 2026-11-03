"""Finish both videos with ffmpeg (run where the recording was made, e.g. GitHub Actions).

    python video/finish.py        -> video/out/night_guard_family_room_demo.mp4
                                     video/out/night_guard_family_room_film.mp4

Demo: the raw recording with each narration line placed at its scene start, over a soft pad.
Film: slides drawn with Pillow (plus frames from the demo), one per narration line.
The pad is synthesized here (A minor drone), so there is no third-party music.
"""

from __future__ import annotations

import json
import subprocess
import textwrap
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from snoozy import sloth

HERE = Path(__file__).resolve().parent
WORK, OUT = HERE / "work", HERE / "out"
W, H, SR = 1920, 1080, 24000
NAVY, INDIGO, AMBER, WHITE, SOFT = (11, 16, 38), (49, 46, 129), (251, 191, 36), (255, 255, 255), (199, 210, 254)


def run(*cmd: str) -> None:
    subprocess.run(cmd, check=True)


def pcm(path: Path) -> np.ndarray:
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-f", "f32le", "-ac", "1", "-ar", str(SR), "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).copy()


def pad(seconds: float) -> np.ndarray:
    t = np.arange(int(seconds * SR)) / SR
    tone = sum(np.sin(2 * np.pi * f * t) * a for f, a in [(110, .5), (164.81, .3), (220, .25), (261.63, .15)])
    tone *= 0.5 + 0.5 * np.sin(2 * np.pi * 0.05 * t) ** 2
    fade = np.minimum(1, np.minimum(t / 3, (seconds - t) / 3))
    return (tone * fade * 0.035).astype(np.float32)


def write_wav(samples: np.ndarray, path: Path) -> None:
    samples = np.clip(samples, -1, 1).astype(np.float32)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", "pipe:0",
                    str(path)], input=samples.tobytes(), check=True)


def duration(path: Path) -> float:
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
                         capture_output=True, text=True, check=True).stdout
    return float(out.strip())


FPS = 30
MASCOT_W, MASCOT_H = 300, 320


def mouth_track(speech: np.ndarray, frames: int) -> np.ndarray:
    """How open Snoozy's mouth is in each video frame: the narration loudness, closed in the pauses."""
    hop = SR / FPS
    rms = np.array([np.sqrt(np.mean(speech[int(i * hop): int((i + 1) * hop)] ** 2) + 1e-12) for i in range(frames)])
    level = rms / (np.percentile(rms[rms > 1e-4], 95) if np.any(rms > 1e-4) else 1)
    level = np.convolve(level, np.ones(3) / 3, mode="same")
    return np.where(level > 0.12, np.clip(level, 0, 1), 0.0)


def mascot_movie(speech: np.ndarray, seconds: float, path: Path) -> Path:
    """Snoozy on a transparent background, lip-synced to `speech`, as a video with alpha."""
    frames = int(seconds * FPS)
    mouth = mouth_track(speech, frames)
    proc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgba", "-s",
                             f"{MASCOT_W}x{MASCOT_H}", "-r", str(FPS), "-i", "pipe:0", "-c:v", "qtrle", str(path)],
                            stdin=subprocess.PIPE)
    for i in range(frames):
        img = Image.new("RGBA", (MASCOT_W, MASCOT_H), (0, 0, 0, 0))
        sloth(img, i / FPS, MASCOT_W // 2, MASCOT_H - 6, 290, float(mouth[i]), "talk", 0.0)
        proc.stdin.write(img.tobytes())
    proc.stdin.close()
    proc.wait()
    return path


def finish_demo() -> Path:
    raw = Path(json.loads((WORK / "raw.json").read_text())["video"])
    scenes = json.loads((WORK / "scenes.json").read_text())
    begin = max(0.0, scenes[0]["start"] - 0.2)  # drop the sign-in pre-roll before the title card
    end_t = min(duration(raw), scenes[-1]["end"] + 0.3)
    # Waits for the agent (Gemma writing on a CPU) are cut, keeping a short beat on each side.
    gaps = [(s["start"] + 1.5, s["at"] - 0.8) for s in scenes if s["at"] - s["start"] > 4]
    keep, t = [], begin
    for g0, g1 in gaps:
        keep.append((t, g0))
        t = g1
    keep.append((t, end_t))

    def new_time(x: float) -> float:
        return sum(max(0.0, min(x, b) - a) for a, b in keep)

    length = sum(b - a for a, b in keep)
    speech = np.zeros(len(pad(length)), np.float32)
    for s in scenes:
        voice = pcm(WORK / "voice" / f"{s['key']}.mp3")
        start = int((new_time(s["at"]) + 0.3) * SR)
        end = min(len(speech), start + len(voice))
        speech[start:end] += voice[: end - start]
    write_wav(speech + pad(length), WORK / "demo_audio.wav")
    mascot = mascot_movie(speech, length, WORK / "snoozy_demo.mov")
    out = OUT / "night_guard_family_room_demo.mp4"
    select = "+".join(f"between(t,{a:.3f},{b:.3f})" for a, b in keep)
    run("ffmpeg", "-v", "error", "-y", "-i", str(raw), "-i", str(WORK / "demo_audio.wav"),
        "-i", str(mascot), "-filter_complex",
        f"[0:v]fps={FPS},select='{select}',setpts=N/{FPS}/TB,scale=1920:1080:flags=lanczos[bg];"
        "[bg][2:v]overlay=24:H-h-8:shortest=1[v]",
        "-map", "[v]", "-map", "1:a", "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p", "-r", "30",
        "-c:a", "aac", "-b:a", "160k", "-af", "loudnorm=I=-14:TP=-1.5", "-shortest", str(out))
    return out


# ── film ───────────────────────────────────────────────────────────────────
def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    name = "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
    for base in ["/usr/share/fonts/truetype/dejavu", "C:/Windows/Fonts"]:
        try:
            return ImageFont.truetype(f"{base}/{name}", size)
        except OSError:
            continue
    return ImageFont.load_default(size)


def canvas() -> tuple[Image.Image, ImageDraw.ImageDraw]:
    img = Image.new("RGB", (W, H), NAVY)
    d = ImageDraw.Draw(img)
    for y in range(H):
        k = y / H
        d.line([(0, y), (W, y)], fill=tuple(int(NAVY[i] * (1 - k) + INDIGO[i] * k) for i in range(3)))
    d.ellipse([W - 260, 80, W - 140, 200], fill=(253, 230, 138))  # the moon
    d.ellipse([W - 230, 62, W - 110, 182], fill=NAVY)
    return img, d


def text_slide(tag: str, title: str, lines: list[str]) -> Image.Image:
    img, d = canvas()
    d.rounded_rectangle([140, 230, 140 + 24 + d.textlength(tag, font(26, True)), 282], 26, fill=AMBER)
    d.text((152, 238), tag, font=font(26, True), fill=(31, 41, 55))
    y = 320
    for line in textwrap.wrap(title, 34):
        d.text((140, y), line, font=font(76, True), fill=WHITE)
        y += 92
    y += 30
    for item in lines:
        for i, line in enumerate(textwrap.wrap(item, 70)):
            d.text((140, y), ("•  " if i == 0 else "    ") + line, font=font(36), fill=SOFT)
            y += 50
        y += 14
    return img


def shot_slide(tag: str, title: str, frame: Path) -> Image.Image:
    img, d = canvas()
    d.text((140, 70), tag, font=font(26, True), fill=AMBER)
    d.text((140, 110), title, font=font(54, True), fill=WHITE)
    shot = Image.open(frame).convert("RGB")
    shot.thumbnail((1420, 800))
    x, y = 120, 220  # leaves the bottom-right corner to Snoozy
    d.rounded_rectangle([x - 8, y - 8, x + shot.width + 8, y + shot.height + 8], 18, fill=(30, 27, 75))
    img.paste(shot, (x, y))
    return img


def flow_slide() -> Image.Image:
    img, d = canvas()
    d.text((140, 90), "HOW IT FLOWS", font=font(26, True), fill=AMBER)
    d.text((140, 130), "Switch is in the middle of every step", font=font(58, True), fill=WHITE)
    box_w, gap = 460, 150
    boxes = [("Child's computer", ["Night Guard", "family rules"]), ("Switch", ["agents · rooms", "threads · documents"]),
             ("Family chat", ["parents approve,", "edit or skip"])]
    for i, (title, sub) in enumerate(boxes):
        x = 140 + i * (box_w + gap)
        fill = (67, 56, 202) if title == "Switch" else (30, 27, 75)
        d.rounded_rectangle([x, 370, x + box_w, 630], 28, fill=fill, outline=SOFT, width=3)
        d.text((x + 34, 410), title, font=font(42, True), fill=WHITE)
        for j, line in enumerate(sub):
            d.text((x + 34, 486 + j * 46), line, font=font(32), fill=SOFT)
        if i < 2:  # arrow in the gap to the next box
            ax = x + box_w + 22
            d.line([(ax, 500), (ax + gap - 70, 500)], fill=AMBER, width=8)
            d.polygon([(ax + gap - 74, 482), (ax + gap - 44, 500), (ax + gap - 74, 518)], fill=AMBER)
    notes = ["Only risk type, app, contact and flagged phrase reach the family room",
             "family-helper writes: talk script · evidence checklist · report text · note to the child",
             "The child is always told, in their own room"]
    y = 700
    for n in notes:
        d.text((140, y), "•  " + n, font=font(34), fill=SOFT)
        y += 58
    return img


def frame_at(video: Path, seconds: float, name: str) -> Path:
    path = WORK / f"{name}.png"
    run("ffmpeg", "-v", "error", "-y", "-ss", f"{seconds:.2f}", "-i", str(video), "-frames:v", "1", str(path))
    return path


def finish_film(demo_raw: Path, scenes: list[dict]) -> Path:
    at = {s["key"]: s["at"] for s in scenes}  # times in the raw recording
    voice = json.loads((WORK / "voice.json").read_text())
    slides = {
        "f0_intro": text_slide("FLIP THE SWITCH · TRACK 02", "Night Guard Family Room",
                               ["Jennifer Evangelista · Florianópolis, Brazil"]),
        "f1_problem": text_slide("THE PROBLEM", "An alert at night, and no idea what to do next",
                                 ["What does it mean?", "What do I say to my child?", "Where do I report it?"]),
        "f2_before": text_slide("ALREADY IN NIGHT GUARD", "The family sees the risk, never the chat",
                                ["Risk type, app, contact and the flagged phrase", "The child is always told",
                                 "Runs on the child's computer with Gemma"]),
        "f3_switch": shot_slide("NEW WITH SWITCH", "The alert lands in the family's group chat",
                                frame_at(demo_raw, at.get("d2_plan", 20) + voice.get("d2_plan", 8) - 1, "f_plan")),
        "f4_flow": shot_slide("THE AGENT WORKS THE CASE", "Parents decide, the agent does the writing",
                              frame_at(demo_raw, at.get("d5_edit", 60) + voice.get("d5_edit", 6), "f_edit")),
        "f5_why": flow_slide(),
        "f6_trust": text_slide("TRUST", "Built so a family can rely on it",
                               ["Safety-critical text is fixed: where to report, don't pay, you're not in trouble",
                                "Only a parent can approve, edit or skip a step",
                                "A test on a real Switch checks every push: nothing beyond the flagged phrase "
                                "reaches the family room"]),
        "f7_end": text_slide("NIGHT GUARD × SWITCH", "Watching out for kids, and helping their parents",
                             ["github.com/jenniferevangelista-de/night-guard-switch"]),
    }
    parts, audio = [], []
    for key, img in slides.items():
        png = WORK / f"{key}.png"
        img.save(png)
        seconds = voice[key] + 0.9
        clip = WORK / f"{key}.mp4"
        run("ffmpeg", "-v", "error", "-y", "-loop", "1", "-i", str(png), "-t", f"{seconds:.2f}",
            "-vf", "fade=in:0:12,fade=out:st=" + f"{seconds - 0.4:.2f}" + ":d=0.4", "-r", str(FPS),
            "-c:v", "libx264", "-pix_fmt", "yuv420p", str(clip))
        parts.append(clip)
        v = pcm(WORK / "voice" / f"{key}.mp3")
        seg = np.zeros(int(seconds * SR), np.float32)
        seg[int(0.3 * SR): int(0.3 * SR) + len(v)] = v[: len(seg) - int(0.3 * SR)]
        audio.append(seg)
    speech = np.concatenate(audio)
    write_wav(speech + pad(len(speech) / SR), WORK / "film_audio.wav")
    mascot = mascot_movie(speech, len(speech) / SR, WORK / "snoozy_film.mov")
    listing = WORK / "film_parts.txt"
    listing.write_text("".join(f"file '{p.as_posix()}'\n" for p in parts))
    out = OUT / "night_guard_family_room_film.mp4"
    run("ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(listing), "-i",
        str(WORK / "film_audio.wav"), "-i", str(mascot), "-filter_complex",
        "[0:v][2:v]overlay=W-w-60:H-h-20:shortest=1[v]", "-map", "[v]", "-map", "1:a",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k",
        "-af", "loudnorm=I=-14:TP=-1.5", "-shortest", str(out))
    return out


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    demo = finish_demo()
    raw = Path(json.loads((WORK / "raw.json").read_text())["video"])
    film = finish_film(raw, json.loads((WORK / "scenes.json").read_text()))
    for f in (demo, film):
        print(f"{f.name}: {duration(f):.0f} s")
