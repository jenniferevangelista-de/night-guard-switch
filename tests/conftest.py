import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


class FakeAgent:
    """Records what an agent would do in Switch, room by room."""

    def __init__(self):
        self.posts: list[dict] = []
        self.docs: dict[str, dict] = {}

    def post(self, room_id, body, thread_id=None):
        self.posts.append({"room": room_id, "body": body, "thread": thread_id, "to": []})
        return f"evt{len(self.posts)}"

    def mention(self, room_id, body, names, thread_id=None):
        self.posts.append({"room": room_id, "body": body, "thread": thread_id, "to": list(names)})
        return {"event_id": f"evt{len(self.posts)}"}

    def create_document(self, room_id, name, description, content, instructions=""):
        doc_id = f"doc{len(self.docs) + 1}"
        self.docs[doc_id] = {"room": room_id, "name": name, "content": content}
        return doc_id

    def update_document(self, room_id, document_id, content):
        self.docs[document_id]["content"] = content

    def find_document(self, room_id, name):
        return next((i for i, d in self.docs.items() if d["name"] == name and d["room"] == room_id), None)

    def load_documents(self, room_id, ids):
        return [{"id": i, "description": "", "content": self.docs[i]["content"]} for i in ids]

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        pass

    def posts_in(self, room):
        return [p for p in self.posts if p["room"] == room]


@pytest.fixture
def fake_agent():
    return FakeAgent()


@pytest.fixture
def state(tmp_path, monkeypatch):
    s = {
        "switch_url": "http://switch.test",
        "agents": {"night-guard": {"id": "a1", "api_key": "k1"}, "family-helper": {"id": "a2", "api_key": "k2"}},
        "rooms": {"family": {"id": "room-family"}, "child": {"id": "room-child"}},
        "parents": ["mom", "dad"],
        "child": {"name": "Lia", "username": "lia"},
        "family_rules": {},
    }
    path = tmp_path / "state.json"
    path.write_text(json.dumps(s))
    monkeypatch.setattr("family_room.config.STATE_FILE", path)
    monkeypatch.setenv("NG_DETECTOR", "replay")
    monkeypatch.setenv("NG_WRITER", "template")
    return s
