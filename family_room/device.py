"""night-guard: the child's device side.

Runs Night Guard's detector on a (fictional) chat, applies the family rules, and then:
  - shared risk  -> posts ONLY risk type, app, contact and flagged phrase into the family room,
                    with the event stored as a room document for family-helper, and tells the
                    child in their own room that the family was told;
  - child decides -> tells only the child, nothing goes to the family;
  - nothing found -> nothing is posted.

    python -m family_room.device snap-secret
"""

from __future__ import annotations

import json
import sys

from nightguard.family import apply_rules
from nightguard.signals import SIGNALS

from . import detect
from .config import DEVICE_AGENT, HELPER_AGENT, load_chat, load_state
from .switch_client import Agent

SEV = {"high": "🔴 HIGH", "medium": "🟠 MEDIUM", "low": "🟡 LOW"}


def alert_text(event: dict, child: str) -> str:
    sig = "\n".join(f"• {s['label']}: \"{s['quote']}\"" for s in event["signals"])
    return (
        f"🌙 Night Guard alert · {SEV.get(event['severity'], event['severity'])} · {event['app']} · contact {event['contact']}\n"
        f"{sig}\n"
        f"Shared by your family rules. {child} was told on their computer. The full chat stays there."
    )


def child_text(event: dict, child: str) -> str:
    kid = "\n".join(f"• {SIGNALS[s['id']]['kid']['en']}" for s in event["signals"])
    if event["shared"]:
        told = ", ".join(s["label"].lower() for s in event["signals"])
        return (f"Hi {child}, it's Night Guard. I saw something risky on {event['app']}:\n{kid}\n\n"
                f"Your family rules say I tell your family about this ({told}). I only shared what was flagged, "
                "not your whole chat. You're not in trouble.")
    return (f"Hi {child}, it's Night Guard. Something on {event['app']} looked off:\n{kid}\n\n"
            "This stays with you. If you want help, you can tell someone you trust.")


def run(chat_id: str) -> dict | None:
    state = load_state()
    chat = load_chat(chat_id)
    child = state["child"]["name"]
    result = detect.analyze(chat)
    event = apply_rules(result, app=chat["app"], contact=chat["contact"], rules=state.get("family_rules"))
    if event is None:
        print(f"{chat_id}: nothing risky found ({result['analysis_status']}), nothing posted.")
        return None
    me = state["agents"][DEVICE_AGENT]
    agent = Agent(state["switch_url"], me["id"], me["api_key"], DEVICE_AGENT)
    family, kid_room = state["rooms"]["family"]["id"], state["rooms"]["child"]["id"]
    if event["shared"]:
        record = {**event, "child": child}
        doc = agent.create_document(
            family, f"alert-{event['id']}", f"Night Guard alert {event['id']}: shared fields only",
            json.dumps(record, ensure_ascii=False, indent=2),
            instructions="Night Guard alert as JSON: risk type, app, contact, flagged phrase. Never the full chat.",
        )
        agent.mention(family, alert_text(event, child) + f"\nng-alert {event['id']} doc {doc}", [HELPER_AGENT])
    agent.post(kid_room, child_text(event, child))
    print(f"{chat_id}: {event['severity']} risk, shared with family: {event['shared']}")
    return event


if __name__ == "__main__":
    run(sys.argv[1] if len(sys.argv) > 1 else "snap-secret")
