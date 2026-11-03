"""The texts family-helper writes.

Night Guard's rule carries over: anything safety-critical is a fixed template (where to report,
"don't pay", "you're not in trouble"). A model is only used to make the explanation and the
talk script sound natural for this family, and to apply a parent's edit. When no model is
configured (NG_WRITER=template, the default) every text comes from the templates below.
"""

from __future__ import annotations

import os

import httpx

GITHUB_MODELS_URL = "https://models.github.ai/inference/chat/completions"

HOTLINE_SIGNALS = {"photo_request", "sextortion"}  # Night Guard: image requests, threats or money demands
APP_REPORT_HELP = {
    "Roblox": "Roblox: open the person's profile, tap the three dots, Report Abuse.",
    "Discord": "Discord: right-click the message, Report Message (or Trust & Safety: dis.gd/report).",
    "Minecraft": "Minecraft (Java): pause menu, Player Reporting, pick the player and the messages. On a server, also tell its moderators.",
    "Instagram": "Instagram: open the profile, the three dots, Report, then 'It's inappropriate'.",
    "TikTok": "TikTok: open the profile, Share, Report.",
    "WhatsApp": "WhatsApp: open the chat, the contact name, Report contact.",
    "Fortnite": "Fortnite: open the player list, select the player, Report Player.",
}
HOTLINES = (
    "Brazil: SaferNet Brasil, https://new.safernet.org.br/denuncie\n"
    "United States and worldwide: NCMEC CyberTipline, https://report.cybertip.org\n"
    "Images already shared: Take It Down (NCMEC), https://takeitdown.ncmec.org"
)


def writer() -> str:
    return os.environ.get("NG_WRITER", "template")


def _model(system: str, user: str) -> str | None:
    """Ask GitHub Models for a short text. Any failure falls back to the template."""
    if writer() != "github":
        return None
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if not token:
        return None
    try:
        r = httpx.post(
            GITHUB_MODELS_URL,
            headers={"Authorization": f"Bearer {token}"},
            json={"model": os.environ.get("NG_GITHUB_MODEL", "openai/gpt-4.1-mini"), "temperature": 0.3,
                  "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}]},
            timeout=60,
        )
        r.raise_for_status()
        text = r.json()["choices"][0]["message"]["content"].strip()
        return text.replace("—", ",") or None  # house style: no em dashes
    except (httpx.HTTPError, KeyError, IndexError, ValueError):
        return None


STYLE = ("You help a parent after a child-safety alert. Plain words, short sentences, warm and calm, no jargon, "
         "no em dashes, never blame the child, never suggest punishment, never invent phone numbers or links. "
         "Use only the facts given.")


def facts(event: dict, child: str) -> str:
    lines = [f"Child: {child}", f"App: {event['app']}", f"Contact: {event['contact']}", f"Risk: {event['severity']}"]
    lines += [f"- {s['label']}: \"{s['quote']}\" ({s['why']})" for s in event["signals"]]
    return "\n".join(lines)


def signal_ids(event: dict) -> set[str]:
    return {s["id"] for s in event["signals"]}


# ── what the parents read first ─────────────────────────────────────────────
def explain(event: dict, child: str) -> str:
    template = " ".join(s["why"] for s in event["signals"])
    text = _model(STYLE, "In 2 or 3 sentences, explain to the parent what this means and why it matters.\n"
                  + facts(event, child))
    return text or template


# ── step outputs ────────────────────────────────────────────────────────────
def talk_script(event: dict, child: str, note: str = "") -> str:
    labels = ", ".join(s["label"].lower() for s in event["signals"])
    template = (
        f"Talk script for {child} (calm, no punishment)\n\n"
        f"Start: \"Night Guard told us something on {event['app']} looked off. You're not in trouble. "
        f"We're proud of you, and we want to understand it together.\"\n\n"
        f"Ask: \"How do you know {event['contact']}? How did that chat make you feel?\"\n\n"
        f"Explain: \"Some people online try tricks like this ({labels}). It isn't your fault, "
        f"and it's exactly the kind of thing you can always bring to us.\"\n\n"
        "Agree together: don't reply, block, and tell us if they come back with another account.\n\n"
        "End: \"Thank you for being honest. You can always tell us, even if you think you'll get in trouble.\""
    )
    if note:
        template += f"\n\nParent's note: {note}"
    text = _model(STYLE, "Write a short talk script (opening line, 2 questions, a kind explanation, what we agree, "
                  "closing line) for the parent to use with the child tonight. Keep the child's dignity."
                  + (f" Apply this request from the parent: {note}" if note else "") + "\n" + facts(event, child))
    return text or template


def evidence_checklist(event: dict, child: str, note: str = "") -> str:
    quotes = "\n".join(f"- \"{s['quote']}\"" for s in event["signals"])
    text = (
        f"Evidence checklist ({event['app']}, contact {event['contact']})\n\n"
        "Do this before blocking, because blocking can hide the chat:\n"
        f"1. Screenshot the messages Night Guard flagged:\n{quotes}\n"
        f"2. Screenshot {event['contact']}'s profile page (name, picture, user id or link).\n"
        "3. Write down the date and time you saw it, and the app.\n"
        "4. Save the screenshots in one folder. Don't forward them to friends or groups.\n"
        "5. Don't delete the chat and don't reply to the contact."
    )
    if "photo_request" in signal_ids(event) or "sextortion" in signal_ids(event):
        text += ("\n\nIf the chat contains images of your child: don't screenshot or save those images. "
                 "Note that they exist and tell the hotline or the police; they will collect them safely.")
    return text + (f"\n\nParent's note: {note}" if note else "")


def app_report(event: dict, child: str, note: str = "") -> str:
    how = APP_REPORT_HELP.get(event["app"], "Use the app's Report option on the profile or the message.")
    reasons = "; ".join(f"{s['label']} (\"{s['quote']}\")" for s in event["signals"])
    text = (
        f"Block and report {event['contact']} on {event['app']}\n\n"
        f"Where: {how}\n\n"
        "Text you can paste in the report:\n"
        f"\"This account is contacting a minor. It sent messages that match grooming tactics: {reasons}. "
        "Please review the account and its other accounts.\"\n\n"
        "Then block the account."
    )
    return text + (f"\n\nParent's note: {note}" if note else "")


def hotline_report(event: dict, child: str, note: str = "") -> str:
    text = (
        "Report to a hotline and the police\n\n"
        f"{HOTLINES}\n\n"
        "What to say: the app, the account name, the date, and what was asked "
        f"({'; '.join(s['label'].lower() for s in event['signals'])}).\n\n"
        "Don't pay and don't send anything. Paying usually brings more demands. "
        "Keep the evidence and contact the police."
    )
    return text + (f"\n\nParent's note: {note}" if note else "")


def child_note(event: dict, child: str, note: str = "") -> str:
    text = (f"Hi {child}, it's Night Guard. Your family saw what I shared about {event['app']}. "
            "You're NOT in trouble. They want to talk with you calmly today. "
            "Until then: don't reply to that person, and don't send anything.")
    return text + (f"\nFrom your parents: {note}" if note else "")


def apply_edit(text: str, note: str) -> str:
    """A parent's edit to a step that is already written: rewrite with the model, else append."""
    rewritten = _model(STYLE, f"Rewrite this text applying the parent's request: {note}\n\nText:\n{text}")
    return rewritten or f"{text}\n\nParent's note: {note}"
