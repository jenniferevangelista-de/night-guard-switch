"""End-to-end check on a running Switch: plays the parents in Mattermost and checks every promise.

    python -m family_room.e2e            (family-helper must be running)

1. snap-secret (shared by the family rules): the alert reaches the family room, family-helper
   explains and proposes steps, nothing is written before approval. The child (Lia) is told.
2. Mom approves steps 1 to 4, dad edits step 2: the documents are posted, Lia gets her note.
3. Privacy: the parts of the chat Night Guard did not flag never reach the family room.
4. whatsapp-number (the child decides): only Lia is told, the family room gets nothing.
5. just-gaming (nothing risky): nothing is posted anywhere.
Writes out/transcript.md with both rooms as the people saw them. Exits non-zero on failure.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

from . import device
from .config import ROOT, load_chat, load_state
from .setup import Mattermost

OUT = ROOT / "out"
failures: list[str] = []


def check(ok: bool, what: str) -> None:
    print(("PASS " if ok else "FAIL ") + what, flush=True)
    if not ok:
        failures.append(what)


def posts(mm: Mattermost, channel: str) -> list[dict]:
    data = mm.get(f"/channels/{channel}/posts?per_page=200").json()
    return sorted((data["posts"][i] for i in data["order"]), key=lambda p: p["create_at"])


def wait_for(mm: Mattermost, channel: str, predicate, seconds: int = 240) -> dict | None:
    end = time.time() + seconds
    while time.time() < end:
        for p in posts(mm, channel):
            if predicate(p):
                return p
        time.sleep(1.5)
    return None


def say(mm: Mattermost, channel: str, text: str, root_id: str) -> None:
    mm.post("/posts", {"channel_id": channel, "message": text, "root_id": root_id}).raise_for_status()


def main() -> int:
    state = load_state()
    url = state["mattermost_url"]
    mom = Mattermost(url, "mom", state["passwords"]["mom"])
    dad = Mattermost(url, "dad", state["passwords"]["dad"])
    lia = Mattermost(url, "lia", state["passwords"]["lia"])
    fam, kid = state["rooms"]["family"]["channel_id"], state["rooms"]["child"]["channel_id"]
    since = int(time.time() * 1000)

    # 1. a shared alert
    event = device.run("snap-secret")
    check(event is not None and event["shared"], "snap-secret is shared by the family rules")
    alert = wait_for(mom, fam, lambda p: p["create_at"] >= since and "Night Guard alert" in p["message"])
    check(alert is not None, "the alert reaches the family room")
    if alert is None:
        return report(mom, lia, fam, kid, since)
    plan = wait_for(mom, fam, lambda p: p.get("root_id") == alert["id"] and "Here's what I suggest" in p["message"])
    check(plan is not None, "family-helper explains the risk and proposes steps in the alert's thread")
    check(wait_for(lia, kid, lambda p: p["create_at"] >= since and "Your family rules say" in p["message"], 30)
          is not None, "Lia is told that her family was told")
    time.sleep(2)
    check(not any("📄 Step" in p["message"] for p in posts(mom, fam) if p["create_at"] >= since),
          "nothing is written before a parent approves")

    # 2. the parents decide
    say(mom, fam, "@family-helper approve 1 3 4", alert["id"])
    check(wait_for(lia, kid, lambda p: p["create_at"] >= since and "You're NOT in trouble" in p["message"]) is not None,
          "after approval, Lia gets the calm note in her own room")
    check(wait_for(mom, fam, lambda p: p.get("root_id") == alert["id"] and "evidence checklist" in p["message"])
          is not None, "the evidence checklist is posted in the thread")
    say(dad, fam, "@family-helper edit 2: she's 10, keep it short and start by saying we love her", alert["id"])
    check(wait_for(mom, fam, lambda p: p.get("root_id") == alert["id"] and "talk script" in p["message"]
                   and "📄" in p["message"]) is not None, "dad's edit produces the talk script")
    say(mom, fam, "@family-helper done 3", alert["id"])
    check(wait_for(mom, fam, lambda p: p.get("root_id") == alert["id"] and "Marked done by mom" in p["message"])
          is not None, "mom marks a step done")

    # 3. privacy
    chat = load_chat("snap-secret")
    quotes = [s["quote"] for s in event["signals"]]  # only what the family rules shared
    leaked = [m["text"] for m in chat["messages"]
              if len(m["text"]) > 8 and m["text"] not in quotes
              and any(m["text"] in p["message"] for p in posts(mom, fam))]
    check(not leaked, f"unflagged parts of the chat never reach the family room {leaked or ''}")

    # 4. the child decides
    before = len(posts(mom, fam))
    device.run("whatsapp-number")
    check(wait_for(lia, kid, lambda p: "This stays with you" in p["message"], 30) is not None,
          "whatsapp-number: only Lia is told")
    time.sleep(3)
    check(len(posts(mom, fam)) == before, "whatsapp-number: nothing reaches the family room")

    # 5. nothing risky
    check(device.run("just-gaming") is None, "just-gaming: nothing is posted")
    return report(mom, lia, fam, kid, since)


def report(mom: Mattermost, lia: Mattermost, fam: str, kid: str, since: int) -> int:
    OUT.mkdir(exist_ok=True)
    names: dict[str, str] = {}

    def who(mm: Mattermost, uid: str) -> str:
        if uid not in names:
            names[uid] = mm.get(f"/users/{uid}").json().get("username", uid)
        return names[uid]

    lines = ["# Transcript of the end-to-end run", ""]
    for title, mm, channel in [("family-safety (mom and dad)", mom, fam), ("lia-night-guard (Lia)", lia, kid)]:
        lines += [f"## {title}", ""]
        for p in posts(mm, channel):
            if p["create_at"] < since or p.get("type"):
                continue
            indent = "> ↳ " if p.get("root_id") else "> "
            body = p["message"].replace("\n", "\n" + indent)
            lines += [f"**{who(mm, p['user_id'])}**", "", indent + body, ""]
    lines += ["## Checks", ""] + [f"- FAIL {f}" for f in failures] + (["- all passed"] if not failures else [])
    Path(OUT / "transcript.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"{'FAILED' if failures else 'ALL PASSED'}; transcript in out/transcript.md")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
