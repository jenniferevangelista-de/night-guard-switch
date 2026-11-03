"""Narration and timeline for the Night Guard Family Room film.

Same format as the Night Guard film (video/script_en.py in the night-guard repo): Snoozy narrates with the
same voice, and his lines from the original film are kept word for word. New here: Jennifer introduces the
project (Ava voice), and Snoozy's new scenes show the Switch family room.

  python video/film_script.py        -> video/work/film_voice/*.mp3 and video/work/film_timeline.json
"""
import asyncio
import json
import subprocess
from pathlib import Path

import edge_tts

HERE = Path(__file__).resolve().parent
OUT = HERE / "work"
SNOOZY = ("en-US-BrianMultilingualNeural", "+0%")   # Snoozy's voice in every Night Guard video
JENNI = ("en-US-AvaMultilingualNeural", "-4%")       # Jennifer, first person

# scene id, voice, narration, extra seconds after the line. "NG" = word for word from the Night Guard film.
SCENES = [
    ("hello", JENNI, "Hi, I'm Jennifer Evangelista, a data engineering and solutions architecture specialist from Brazil. "
                     "Night Guard, my child-safety app, won Best Use of Backboard. For Flip the Switch, I gave it a family "
                     "room. Snoozy will show you.", 0.8),
    ("intro", SNOOZY, "Hi, I'm Snoozy, the laziest night watchman you'll ever meet. Slow and steady is my thing. So let me "
                      "show you how a lazy guard helps keep kids safe.", 0.8),                                      # NG
    ("night", SNOOZY, "It's eleven p.m. A kid is playing online. And someone is being way too nice to her.", 1.4),   # NG
    ("stat", SNOOZY, "In 2025 alone, the US National Center for Missing and Exploited Children received more than fifty "
                     "thousand sextortion reports. That's one hundred thirty seven a day. Almost one every ten minutes.", 1.2),  # NG
    ("fast", SNOOZY, "And it can be fast. In a Swansea University study, the first sexual request came in just eighteen "
                     "minutes.", 1.0),                                                                              # NG
    ("platforms", SNOOZY, "Roblox, Discord, Minecraft, TikTok. Each platform only watches its own backyard. And predators "
                          "know it: they pull the kid into an encrypted app, where no one else can see.", 1.2),      # NG
    ("parents", SNOOZY, "Parents can't read every chat. And kids don't always spot the trap.", 1.4),                 # NG
    ("guard", SNOOZY, "Meet Night Guard. An open model that runs on the family's own computer. It reads what's on the "
                      "screen, so it protects even inside encrypted apps. And the chat never leaves home.", 0.8),    # NG
    ("alert", SNOOZY, "When a stranger asks for a secret, it warns the kid right away, in words they understand.", 10.6),  # NG
    ("family", SNOOZY, "To parents, it's the Night Guard. One alert, not the whole chat. What happened, and what to do now, "
                       "right on their phone.", 1.4),                                                               # NG
    ("after", SNOOZY, "But an alert at night is scary. What does it mean? What do I say? Where do I report it? Until now, "
                      "parents figured that out alone.", 1.0),
    ("room", SNOOZY, "Now the alert lands in the family's group chat, through Switch. Only the flagged phrase. Never the "
                     "chat.", 1.0),
    ("helper", SNOOZY, "A second agent, family helper, explains the risk in plain words and proposes the next steps. Then "
                       "it waits. Only a parent can decide.", 1.0),
    ("decide", SNOOZY, "Mom approves. Dad edits the talk script: she's ten, keep it short. The agent writes every step, "
                       "saves it as a room document, and keeps a case note.", 1.0),
    ("kid", SNOOZY, "And the kid is always told. In her own room, she reads that she is not in trouble.", 1.2),
    ("threat", SNOOZY, "For threats or money demands, it adds SaferNet and NCMEC, and says: don't pay. That text is fixed, "
                       "never improvised.", 1.0),
    ("tech", SNOOZY, "Under the hood: two Switch agents, two linked rooms, threads, targeted messages and room documents, "
                     "on Mattermost. Gemma writes on the family's own machine. And a test on a real Switch runs on every "
                     "push. It checks that only the flagged phrase reaches the parents.", 1.0),
    ("peace", SNOOZY, "Peace for the kid. Peace for the parents. And the more the kid learns, the more the guard can rest.", 1.6),  # NG
    ("end", SNOOZY, "Night Guard Family Room. A partner for parents, a friend for kids, and now a plan for the whole "
                    "family. And me? Back to my nap.", 3.0),
]


async def speak(text, voice, out):
    await edge_tts.Communicate(text, voice[0], rate=voice[1]).save(str(out))


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
        print(f"{s['id']:9} {s['start']:6.2f} -> {s['end']:6.2f}  ({s['voice_dur']}s voice)")
    print("total", round(t + 0.3, 2), "s")


if __name__ == "__main__":
    asyncio.run(main())
