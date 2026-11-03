"""Night Guard family rules. PRE-EXISTING: copied from github.com/jenniferevangelista-de/night-guard
(guard/family.py at commit 7a30a2f, MIT), before this hackathon.

Kids don't always recognize a bad intention, so some signals are shared with the
family automatically. The child is always told when that happens (no secret
monitoring), and the family sees the risk type and the flagged phrase, never
the whole conversation.

Changed for this project: apply_rules() no longer writes to a local file. The event now
travels to the family through Switch (family_room/device.py).
"""

import time
import uuid

from .signals import SIGNAL_IDS

# "tell": the family is told automatically. "child": the child decides.
DEFAULT_RULES = {s: "child" for s in SIGNAL_IDS} | {
    "photo_request": "tell",
    "meet_offline": "tell",
    "credential_request": "tell",
    "secrecy": "tell",
    "returning_after_block": "tell",
    "sextortion": "tell",
}
APPS = ["Roblox", "Minecraft", "Fortnite", "Discord", "TikTok", "Instagram", "WhatsApp", "Other"]


def apply_rules(result, app="Other", contact="", rules=None):
    """Build the event for a flagged check and decide if the family is told.

    Returns the event (with "shared"), or None if nothing was flagged.
    """
    if not result["signals"]:
        return None
    rules = DEFAULT_RULES | {k: v for k, v in (rules or {}).items()
                             if k in SIGNAL_IDS and v in ("tell", "child")}
    triggered = [s for s in result["signals"] if rules.get(s["id"]) == "tell"]
    if result["severity"] == "high" and not triggered:
        triggered = list(result["signals"])  # serious combinations are always shared
    event = {
        "id": uuid.uuid4().hex[:8],
        "time": time.strftime("%Y-%m-%d %H:%M"),
        "app": app if app in APPS else "Other",
        "contact": contact[:40],
        "severity": result["severity"],
        "shared": bool(triggered),
        "signals": [{"id": s["id"], "label": s["label"], "quote": s.get("quote", ""),
                     "why": s.get("parent", "")}
                    for s in (triggered or result["signals"])],
        "steps": result.get("parent_steps", []),
    }
    return event
