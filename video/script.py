"""Narration for the two videos, in Jennifer's first person (voice: en-US-AvaMultilingualNeural).

    python video/script.py        writes video/work/voice/<scene>.mp3 and video/work/voice.json (durations)
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

WORK = Path(__file__).resolve().parent / "work"
VOICE = "en-US-AvaMultilingualNeural"

DEMO = {
    "d0_title": "Hi, I'm Jennifer Evangelista, a data engineering and solutions architecture specialist from Brazil. "
                "This is Night Guard Family Room, a workflow I built with Switch.",
    "d1_alert": "Night Guard is my child-safety app. It runs on the child's computer and spots grooming tactics. "
                "It just found one in a fictional Roblox chat, and Switch delivers the alert to the family's group chat. "
                "Only the flagged phrase is shared, never the whole chat.",
    "d2_plan": "A second Switch agent, family-helper, reads the alert document, explains the risk in plain words, "
               "and proposes four steps. Then it waits. Nothing is written or sent until a parent decides.",
    "d3_approve": "Mom approves steps one, three and four, right in the thread.",
    "d4_outputs": "The agent sends Lia a calm note in her own room, writes the evidence checklist, and drafts the report "
                  "for Roblox. Every output is also saved as a Switch room document, with a case note of who decided what.",
    "d5_edit": "Dad asks for a change to the talk script: she's ten, keep it short. The agent writes it with his note.",
    "d6_child": "This is Lia's view. Night Guard told her the moment her family was told, "
                "and the note from her parents says she is not in trouble.",
    "d7_threat": "When there are threats or money demands, the plan adds SaferNet and NCMEC and says: don't pay. "
                 "Those lines are fixed templates, never improvised by a model.",
    "d8_end": "Switch is the backbone here: two agents, two linked rooms, threads, targeted messages and room documents. "
              "Clone the repository, run one script, and the whole flow runs on your own Switch. Thanks for watching.",
}

FILM = {
    "f0_intro": "Hi, I'm Jennifer Evangelista, a data engineering and solutions architecture specialist from Brazil. "
                "Let me show you why I connected Night Guard to Switch.",
    "f1_problem": "A parent gets a scary alert at night. A stranger asked their child to keep a secret, or sent a threat. "
                  "In that moment it's hard to know what it means, what to say, and where to report.",
    "f2_before": "Night Guard already decided what the family should see: the risk type, the app, the contact "
                 "and the flagged phrase. Never the whole chat. And the child is always told.",
    "f3_switch": "What was missing was the part after the alert. With Switch, the alert lands in the family's group chat, "
                 "and an agent works the case with the parents.",
    "f4_flow": "It explains, proposes steps, and waits for a parent to approve, edit or skip each one. "
               "Then it writes the talk script, the evidence checklist, the report text, and a calm note to the child.",
    "f5_why": "Switch gives me agents, rooms on a normal chat app, threads, targeted messages and documents, "
              "on a server the family controls. Without it, there is no room, no approval and no output.",
    "f6_trust": "Safety-critical text stays fixed. Only parents can decide. And a test on a real Switch "
                "checks on every push that nothing beyond the flagged phrase ever reaches the family room.",
    "f7_end": "Night Guard watches out for kids. Now, with Switch, it also helps their parents know what to do next.",
}


def generate(lines: dict[str, str]) -> dict[str, float]:
    out = WORK / "voice"
    out.mkdir(parents=True, exist_ok=True)
    lengths = {}
    for key, text in lines.items():
        mp3 = out / f"{key}.mp3"
        if not mp3.exists():
            rate = "-4%" if key.endswith(("title", "intro")) else "+2%"
            subprocess.run(["edge-tts", "--voice", VOICE, f"--rate={rate}", "--text", text,
                            "--write-media", str(mp3)], check=True)
        probe = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                                str(mp3)], capture_output=True, text=True, check=True)
        lengths[key] = float(probe.stdout.strip())
    return lengths


if __name__ == "__main__":
    lengths = generate({**DEMO, **FILM})
    (WORK / "voice.json").write_text(json.dumps(lengths, indent=2))
    print(f"{len(lengths)} lines, {sum(lengths.values()):.0f} s of narration")
