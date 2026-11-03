"""Where the setup keeps ids and keys (a local, git-ignored file) and the family's settings."""

from __future__ import annotations

import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STATE_FILE = Path(os.environ.get("NG_STATE", ROOT / ".state.json"))
CHATS_FILE = ROOT / "scenarios" / "chats.json"

DEVICE_AGENT = "night-guard"
HELPER_AGENT = "family-helper"


def load_state() -> dict:
    if not STATE_FILE.exists():
        raise SystemExit(f"No {STATE_FILE.name}: run `python -m family_room.setup` first.")
    return json.loads(STATE_FILE.read_text(encoding="utf-8"))


def save_state(state: dict) -> None:
    STATE_FILE.write_text(json.dumps(state, indent=2), encoding="utf-8")


def load_chat(chat_id: str) -> dict:
    chats = json.loads(CHATS_FILE.read_text(encoding="utf-8"))["chats"]
    for chat in chats:
        if chat["id"] == chat_id:
            return chat
    raise SystemExit(f"Unknown chat {chat_id!r}. Choose one of: {', '.join(c['id'] for c in chats)}")
