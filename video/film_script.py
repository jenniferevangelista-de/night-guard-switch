"""Narration and timeline for the Night Guard Family Room film.

Same format as the Night Guard film (video/script_en.py in the night-guard repo), opened by Jennifer in the
first person (Ava voice); Snoozy, Night Guard's little guard, tells the rest as himself. Lines marked NG are word for word from the Night Guard film. Every number is real:
the Night Guard ones come from its evaluation (eval/last_results.json: 70 fictional chats, gemma4:e4b), the
Switch ones from this repository's tests and end-to-end check.

  python video/film_script.py        -> video/work/film_voice/*.mp3 and video/work/film_timeline.json
"""
import asyncio
import json
import subprocess
from pathlib import Path

import edge_tts

HERE = Path(__file__).resolve().parent
OUT = HERE / "work"
JENNI = ("en-US-AvaMultilingualNeural", "-4%", "+0Hz")     # Jennifer, first person, as herself
SNOOZY = ("en-US-AvaMultilingualNeural", "+6%", "+14Hz")   # Snoozy, Night Guard's little guard, as himself (like Shieldy)

# scene id, voice, narration, extra seconds after the line
SCENES = [
    ("hello", JENNI, "Hi, I'm Jennifer Evangelista, a data engineering and solutions architecture specialist from Brazil. "
                     "I built Night Guard, a child-safety app that runs on the family's own computer, and it won Best Use "
                     "of Backboard. For Flip the Switch, I gave it a family room. Snoozy will show you.", 0.8),
    ("intro", SNOOZY, "Hi! I'm Snoozy, Night Guard's little guard. I watch over kids' chats, right on their own computer.", 0.8),
    ("night", SNOOZY, "It's eleven p.m. A kid is playing online. And someone is being way too nice to her.", 1.4),    # NG
    ("stat", SNOOZY, "In 2025 alone, the US National Center for Missing and Exploited Children received more than fifty "
                     "thousand sextortion reports. That's one hundred thirty seven a day. Almost one every ten minutes.", 1.2),  # NG
    ("fast", SNOOZY, "And it can be fast. In a Swansea University study, the first sexual request came in just eighteen "
                     "minutes.", 1.0),                                                                               # NG
    ("guard", SNOOZY, "That's where I come in. Night Guard reads the chat right on the kid's computer, with Gemma, an open "
                      "model. The chat never leaves home.", 0.8),
    ("results", SNOOZY, "In Jennifer's tests on seventy fictional chats, we caught thirty six out of thirty six risky ones, "
                        "with three false alarms in thirty four safe ones, in about three and a half seconds per check. I "
                        "know fourteen grooming tactics.", 1.2),
    ("alert", SNOOZY, "When a stranger asks for a secret, I warn the kid right away, in words they understand.", 10.6),
    ("before", SNOOZY, "But then what? Before, a parent got one alert on the phone, late at night, alone. What does it mean? "
                       "What do I say? Where do I report it?", 1.2),
    ("room", SNOOZY, "Now, with Switch, the alert lands in the family's group chat. Only the flagged phrase. Never the "
                     "chat.", 1.0),
    ("helper", SNOOZY, "A second agent, family helper, explains it in plain words and proposes the next steps, in about a "
                       "second and a half. Then it waits. Only a parent can decide.", 1.0),
    ("decide", SNOOZY, "Mom approves. Dad edits the talk script: she's ten, keep it short. The agent writes every step and "
                       "saves it as a document in the room.", 1.0),
    ("kid", SNOOZY, "And the kid is always told, in her own room: you're not in trouble.", 1.2),
    ("threat", SNOOZY, "For threats or money demands, it adds SaferNet and NCMEC, and says: don't pay. That text is fixed, "
                       "never improvised.", 1.0),
    ("beforeafter", SNOOZY, "So, before: one scary alert, a parent alone, no plan. After: the whole family, a clear plan, "
                            "and the kid in the loop.", 1.2),
    ("proof", SNOOZY, "And it's tested for real. On every push, thirteen checks run on a real Switch server, with two agents "
                      "and two linked rooms. Zero lines of the private chat ever reach the parents.", 1.2),
    ("end", SNOOZY, "Night Guard Family Room. A partner for parents, a friend for kids, and a plan for the whole family. "
                    "Bye for now!", 3.0),
]


async def speak(text, voice, out):
    await edge_tts.Communicate(text, voice[0], rate=voice[1], pitch=voice[2]).save(str(out))


def duration(p):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(p)],
                       capture_output=True, text=True)
    return float(r.stdout.strip())


async def main():
    (OUT / "film_voice").mkdir(parents=True, exist_ok=True)
    t, timeline = 1.2, []
    for i, (sid, voice, line, extra) in enumerate(SCENES, 1):
        out = OUT / "film_voice" / f"n{i:02d}.mp3"
        await speak(line, voice, out)
        d = duration(out)
        timeline.append({"id": sid, "who": "jenni" if voice is JENNI else "snoozy", "line": line, "voice": out.name,
                         "start": round(t, 2), "voice_dur": round(d, 2), "end": round(t + d + extra, 2)})
        t += d + extra
    (OUT / "film_timeline.json").write_text(json.dumps({"scenes": timeline, "duration": round(t + 0.3, 2)},
                                                       indent=2, ensure_ascii=False), encoding="utf-8")
    for s in timeline:
        print(f"{s['id']:12} {s['start']:6.2f} -> {s['end']:6.2f}  ({s['voice_dur']}s voice)")
    print("total", round(t + 0.3, 2), "s")


if __name__ == "__main__":
    asyncio.run(main())
