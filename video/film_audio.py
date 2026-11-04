"""Mix for the Night Guard Family Room film. PRE-EXISTING: the Night Guard film mix (video/ng_audio_en.py in
github.com/jenniferevangelista-de/night-guard): an original drama bed (A minor, piano + strings + heartbeat) until
Night Guard appears, then Funkorama (Kevin MacLeod, CC BY 4.0); Snoozy narrates; Sarah speaks the app's real warning.
New: Jennifer's intro and the sound effects of the Switch scenes."""
import subprocess
from pathlib import Path

import numpy as np
import soundfile as sf

from film import DUR, FAMILY_AT, FAMILY_FILE, MUSIC_SWITCH, S, SARAH_AT, SARAH_FILE, WORK, say, timeline  # noqa: F401

HERE = Path(__file__).resolve().parent
SR = 48000; N = int(SR * DUR); rng = np.random.default_rng(7)
FUNK = HERE / "ng" / "music" / "Funkorama.mp3"


def T(s): return int(s * SR)
def tt(d): return np.arange(int(d * SR)) / SR
def hz(m): return 440.0 * 2 ** ((m - 69) / 12)
def lpf(x, k):
    k = max(1, int(k)); c = np.cumsum(np.concatenate([np.zeros(k), x])); return (c[k:] - c[:-k]) / k


def load(p):
    tmp = WORK / "tmp_mix.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(p), "-ac", "1", "-ar", str(SR), str(tmp)], check=True)
    a, _ = sf.read(tmp, dtype="float64"); tmp.unlink(); return a


def add(buf, t0, s, g=1.0):
    i = T(t0)
    if i >= N: return
    j = min(N, i + len(s)); buf[i:j] += s[: j - i] * g


# ---- original drama bed: Am - F - Dm - E, 4 s per chord, string pad + low piano + heartbeat
def drama(dur):
    n = int(dur * SR); out = np.zeros(n)
    prog = [(57, [57, 60, 64]), (53, [53, 57, 60]), (50, [50, 53, 57]), (52, [52, 56, 59])]
    step = 4.0
    for k in range(int(dur / step) + 1):
        root, ch = prog[k % 4]; t0 = k * step; m = int(step * SR * 1.15)
        t = np.arange(m) / SR; env = np.minimum(1, t / 1.2) * np.minimum(1, (step * 1.15 - t) / 0.8).clip(0)
        pad = sum(np.sin(2 * np.pi * hz(x) * (1 + dt) * t) + 0.35 * np.sin(4 * np.pi * hz(x) * (1 + dt) * t)
                  for x in ch for dt in (-0.003, 0.003))
        add_local(out, t0, pad * env * 0.05)
        bass = np.sin(2 * np.pi * hz(root - 24) * t) * env * 0.12
        add_local(out, t0, bass)
        for b, x in enumerate([ch[0] + 12, ch[2] + 12, ch[1] + 12, ch[2] + 12]):     # slow piano notes
            pt = np.arange(int(1.6 * SR)) / SR
            note = sum(np.sin(2 * np.pi * hz(x) * h * pt) / h ** 1.5 for h in (1, 2, 3)) * np.exp(-pt * 2.2) * 0.07
            add_local(out, t0 + b * 1.0, note)
    for i in range(int(dur / 1.15)):                                                     # heartbeat
        bt = np.arange(int(0.25 * SR)) / SR
        beat = np.sin(2 * np.pi * (55 + 30 * np.exp(-bt * 30)) * bt) * np.exp(-bt * 18) * 0.35
        add_local(out, i * 1.15, beat); add_local(out, i * 1.15 + 0.28, beat * 0.7)
    return out


def add_local(buf, t0, s):
    i = int(t0 * SR)
    if i >= len(buf): return
    j = min(len(buf), i + len(s)); buf[i:j] += s[: j - i]


voice = np.zeros(N); sfx = np.zeros(N)
for s in timeline().values():
    v = load(WORK / "film_voice" / s["voice"]); add(voice, s["start"], v / (np.abs(v).max() + 1e-9) * 0.9)
v = load(SARAH_FILE); add(voice, SARAH_AT, v / (np.abs(v).max() + 1e-9) * 0.9)
v = load(FAMILY_FILE); add(voice, FAMILY_AT, v / (np.abs(v).max() + 1e-9) * 0.9)   # tell your parents

def pop(): t = tt(0.18); return np.sin(2 * np.pi * (700 + 900 * t) * t) * np.exp(-t * 28) * 0.5
# No noise-based effects (no hiss): every effect is made of tones.
def thud(): t = tt(0.35); return np.sin(2 * np.pi * (90 + 120 * np.exp(-t * 25)) * t) * np.exp(-t * 12)
def poofs(): t = tt(0.6); f = 520 - 260 * t / 0.6; return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.sin(np.pi * t / 0.6) ** 2 * 0.45
def chime(f0=1320): t = tt(0.6); return sum(np.sin(2 * np.pi * f0 * m * t) / m for m in (1, 2, 3)) * np.exp(-t * 5) * 0.25
def swish(): t = tt(0.25); f = 500 + 1500 * t / 0.25; return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.sin(np.pi * t / 0.25) ** 2 * 0.22
def alarm(): t = tt(0.5); return np.sin(2 * np.pi * 660 * t) * (np.sin(2 * np.pi * 4 * t) > 0) * np.exp(-t * 3) * 0.15
def tick(): t = tt(0.05); return np.sin(2 * np.pi * 2400 * t) * np.exp(-t * 120) * 0.4

n0 = S("night")["start"] - 1.2
for t0 in (2.2, 3.8, 5.6, 7.4): add(sfx, n0 + t0, pop())
add(sfx, S("hello")["start"] + 0.2, chime(1320), 0.8); add(sfx, S("hello")["start"] + 0.35, chime(1760), 0.8)
add(sfx, say("hello", "Best Use"), thud(), 0.7); add(sfx, say("hello", "Flip the Switch"), thud(), 0.7)
a = S("stat")["start"]; add(sfx, a + 7.0, thud()); add(sfx, a + 8.6, thud(), 0.7)
a = S("fast")["start"]
for i in range(10): add(sfx, a + 0.5 + i * 0.5, tick())
a = S("guard")["start"]; add(sfx, a + 1.3, poofs()); add(sfx, a + 1.5, chime(880)); add(sfx, a + 1.65, chime(1320))
add(sfx, say("guard", "Gemma"), thud(), 0.6)
for kw in ("thirty six out", "three false", "three and a half", "fourteen"): add(sfx, say("results", kw), chime(1047), 0.7)
add(sfx, SARAH_AT - 0.8, alarm()); add(sfx, SARAH_AT - 0.3, thud(), 0.6)
add(sfx, S("before")["start"] + 0.2, thud(), 0.8)
for kw in ("mean", "say", "report"): add(sfx, say("before", kw) - 0.2, tick(), 0.9)
add(sfx, S("room")["start"] + 0.2, chime(1568)); add(sfx, S("room")["start"] + 0.32, chime(2093))
add(sfx, say("room", "Switch"), poofs(), 0.6); add(sfx, say("room", "group chat"), swish())
add(sfx, say("room", "Never"), thud(), 0.6)
add(sfx, S("helper")["start"] + 0.2, swish()); add(sfx, say("helper", "second and a half"), chime(1320))
add(sfx, say("helper", "waits"), thud(), 0.8)
add(sfx, S("decide")["start"], swish()); add(sfx, say("decide", "Dad"), swish()); add(sfx, say("decide", "document"), thud(), 0.7)
add(sfx, S("kid")["start"] + 0.2, swish()); add(sfx, say("kid", "not in trouble"), chime(1760))
add(sfx, S("threat")["start"] + 0.2, swish()); add(sfx, say("threat", "SaferNet"), pop()); add(sfx, say("threat", "NCMEC"), pop())
add(sfx, say("threat", "don't pay"), thud())
add(sfx, S("beforeafter")["start"] + 0.2, thud(), 0.7)
for kw in ("one scary", "alone", "no plan"): add(sfx, say("beforeafter", kw), tick(), 0.9)
for kw in ("whole family", "clear plan", "kid in"): add(sfx, say("beforeafter", kw), chime(1320), 0.6)
for kw in ("thirteen", "two agents", "Zero"): add(sfx, say("proof", kw), chime(1047), 0.8)
a = S("end")["start"]; add(sfx, a, chime(880), 1.0); add(sfx, a + 0.15, chime(1320), 1.0)

# music: drama until the guard arrives, 2 s crossfade into Funkorama
ds = T(max(0.0, S("night")["start"] - 0.6)); dr = np.zeros(N); d = drama(MUSIC_SWITCH + 3)[: N - ds]; dr[ds:ds + len(d)] = d; dr = dr / (np.abs(dr).max() + 1e-9)
fk = load(FUNK)
while len(fk) < N: fk = np.concatenate([fk, fk])
fk = fk[:N] / (np.abs(fk).max() + 1e-9)
x = np.clip((np.arange(N) / SR - MUSIC_SWITCH) / 2.0, 0, 1)
music = dr * (1 - x) * 0.55 + fk * x * 0.30
music[ds:ds + T(1.5)] *= np.linspace(0, 1, T(1.5))
music[:ds] += fk[:ds] * 0.12                                  # light tune under the hellos
duck = lpf((np.abs(voice) > 0.02).astype(float), SR // 4); duck = 1 - 0.55 * np.clip(duck * 3, 0, 1)
fade = np.ones(N); fade[T(DUR - 2.5):] = np.linspace(1, 0, N - T(DUR - 2.5))
mix = voice + sfx * 0.7 + music * duck * fade
mix = np.tanh(mix * 0.9) / np.tanh(0.9); mix = mix / np.abs(mix).max() * 0.95
sf.write(WORK / "film_mix.wav", np.stack([mix, mix], 1), SR); print("ok", DUR)
