"""Narration for the tour (a real recording of Switch + Mattermost), in the Night Guard tour format:
Jennifer narrates every part in the first person, with the same voice and pace as in the film.

  python video/tour_script.py      -> video/work/voice/<scene>.mp3 and video/work/voice.json (durations)
"""
import asyncio
import json
import subprocess
import sys
from pathlib import Path

import edge_tts

sys.path.insert(0, str(Path(__file__).resolve().parent))
from film_script import SCENES as FILM_SCENES  # noqa: E402

WORK = Path(__file__).resolve().parent / "work"
JENNI = ("en-US-AvaMultilingualNeural", "-4%")    # exactly as in the film, then 20% faster like the film

# scene key (as in record_demo.py), title beside the recording, voice, line
LINES = [
    ("d0_title", "Hello", JENNI, FILM_SCENES[0][2]),   # Jennifer's opening, the same line as the film
    ("d1_alert", "The alert", JENNI, "This is a real run. Night Guard just found a risk in a fictional Roblox chat, and "
                                     "Switch posts the alert in the family room: only the flagged phrase, never the chat."),
    ("d2_plan", "The plan", JENNI, "Family helper reads the alert document, explains it in plain words, and proposes four "
                                   "steps. Then it waits for a parent."),
    ("d3_approve", "Mom decides", JENNI, "Mom approves steps one, three and four, right in the thread."),
    ("d4_outputs", "The agent works", JENNI, "The agent sends Lia her note, and writes the evidence checklist and the "
                                             "report text for Roblox. Each one is saved as a room document."),
    ("d5_edit", "Dad edits", JENNI, "Dad edits the talk script: she's ten, keep it short. Gemma rewrites it on the "
                                    "family's own machine."),
    ("d6_child", "Lia's room", JENNI, "This is Lia's own room. Night Guard told her the moment her family was told. "
                                      "She's not in trouble."),
    ("d7_threat", "Threats", JENNI, "A threat with a money demand? The plan adds SaferNet and NCMEC, and says: don't pay. "
                                    "That text is fixed."),
    ("d8_end", "Night Guard Family Room", JENNI, "Two agents, two rooms, threads and documents, all through Switch, and "
                                                 "thirteen checks on every push. Night Guard Family Room: a partner for "
                                                 "parents, a friend for kids."),
]


def duration(p):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(p)],
                         capture_output=True, text=True, check=True).stdout
    return float(out.strip())


if __name__ == "__main__":
    (WORK / "voice").mkdir(parents=True, exist_ok=True)
    lengths, meta = {}, []
    for key, title, (voice, rate), line in LINES:
        mp3 = WORK / "voice" / f"{key}.mp3"
        asyncio.run(edge_tts.Communicate(line, voice, rate=rate).save(str(mp3)))   # same call as the film
        if voice == JENNI[0]:   # the film plays 20% faster; her opening here sounds exactly like it does there
            raw = mp3.with_name(mp3.stem + "_raw.mp3")
            mp3.rename(raw)
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(raw), "-filter:a", "atempo=1.2", str(mp3)], check=True)
            raw.unlink()
        lengths[key] = duration(mp3)
        meta.append({"id": key, "title": title, "who": "jenni" if voice == JENNI[0] else "snoozy", "line": line,
                     "voice": f"voice/{key}.mp3", "dur": round(lengths[key], 2)})
    (WORK / "voice.json").write_text(json.dumps(lengths, indent=2))
    (WORK / "tour_narration.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"{len(meta)} lines, {sum(lengths.values()):.0f} s of narration")
