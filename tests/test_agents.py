import json

import pytest

from family_room import device, helper
from family_room.switch_client import parse_sse


@pytest.fixture
def wired(state, fake_agent, monkeypatch, tmp_path):
    monkeypatch.setattr(device, "Agent", lambda *a, **k: fake_agent)
    fh = helper.FamilyHelper(fake_agent, state, cases_file=tmp_path / "cases.json")
    return fake_agent, fh


def message(sender, body, thread_id=None, message_id="m1", room="room-family"):
    return {"type": "message", "room_id": room,
            "payload": {"sender_name": sender, "body": body, "thread_id": thread_id, "message_id": message_id}}


def deliver_alert(agent, fh):
    alert = agent.posts_in("room-family")[-1]
    fh.handle(message("night-guard", alert["body"], message_id="alert-1"))
    return "alert-1"


def test_device_shares_only_what_rules_allow(wired):
    agent, _ = wired
    event = device.run("snap-secret")
    family = agent.posts_in("room-family")
    assert len(family) == 1 and family[0]["to"] == ["family-helper"]
    body = family[0]["body"]
    assert "don't tell your parents ok?" in body
    for hidden in ("mature for your age", "add me there", "they wouldn't get it"):
        assert hidden not in body
    doc = json.loads(next(iter(agent.docs.values()))["content"])
    assert doc["id"] == event["id"] and doc["child"] == "Lia" and "messages" not in doc
    kid = agent.posts_in("room-child")
    assert len(kid) == 1 and "Your family rules say I tell your family" in kid[0]["body"]


def test_device_child_decides(wired):
    agent, _ = wired
    device.run("whatsapp-number")
    assert agent.posts_in("room-family") == []
    assert "This stays with you" in agent.posts_in("room-child")[0]["body"]


def test_device_nothing_found(wired):
    agent, _ = wired
    assert device.run("just-gaming") is None and agent.posts == []


def test_helper_full_case(wired):
    agent, fh = wired
    device.run("snap-secret")
    thread = deliver_alert(agent, fh)
    plan = agent.posts_in("room-family")[-1]
    assert plan["thread"] == thread and plan["to"] == ["mom", "dad"]
    assert "Here's what I suggest" in plan["body"] and "1. Send Lia a calm note" in plan["body"]
    case = next(iter(fh.cases.values()))
    assert agent.docs[case.note_document_id]["name"] == f"case-{case.id}"

    # the child (or anyone who isn't a parent) cannot decide
    fh.handle(message("lia", "@family-helper approve", thread_id=thread))
    assert "Only a parent" in agent.posts_in("room-family")[-1]["body"]
    assert all(s.status == "proposed" for s in case.steps)

    fh.handle(message("mom", "@family-helper approve 1 3", thread_id=thread))
    kid = agent.posts_in("room-child")
    assert "You're NOT in trouble" in kid[-1]["body"]
    assert any("evidence checklist" in p["body"] for p in agent.posts_in("room-family"))
    assert case.steps[0].status == "done" and case.steps[2].status == "approved"

    fh.handle(message("dad", "@family-helper edit 2: start by saying we love her", thread_id=thread))
    talk = agent.docs[case.steps[1].document_id]["content"]
    assert "start by saying we love her" in talk
    note = agent.docs[case.note_document_id]["content"]
    assert "mom approved" in note and "dad edited step 2" in note

    saved = json.loads(fh.cases_file.read_text())
    assert case.id in saved


def test_helper_ignores_chatter_and_other_rooms(wired):
    agent, fh = wired
    device.run("snap-secret")
    thread = deliver_alert(agent, fh)
    n = len(agent.posts)
    fh.handle(message("mom", "thanks, talking to her tonight", thread_id=thread))
    fh.handle(message("mom", "@family-helper approve", thread_id=thread, room="room-other"))
    fh.handle(message("mom", "@family-helper approve", thread_id="another-thread"))
    assert len(agent.posts) == n


def test_parent_names_from_switch_ids(state, fake_agent, tmp_path):
    fh = helper.FamilyHelper(fake_agent, state, cases_file=None)
    assert fh.parent_name({"sender_name": "Mom"}) == "mom"
    assert fh.parent_name({"sender_name": "Dad Silva"}) == "dad"
    assert fh.parent_name({"sender_name": "lia"}) is None


def test_parse_sse():
    lines = [": keepalive", "id: 7", "event: message", 'data: {"type":"message","sequence":7}', "",
             'data: {"type":"connection_state"}', ""]
    assert [e["type"] for e in parse_sse(iter(lines))] == ["message", "connection_state"]
    no_blank_lines = [x for x in lines if x]
    assert [e["type"] for e in parse_sse(iter(no_blank_lines))] == ["message", "connection_state"]
    split = ['data: {"type":', 'data: "message"}', ""]
    assert [e["type"] for e in parse_sse(iter(split))] == ["message"]


def test_hotline_case_for_threats(wired):
    agent, fh = wired
    device.run("gift-card-threat")
    thread = deliver_alert(agent, fh)
    fh.handle(message("mom", "approve", thread_id=thread))
    assert any("Don't pay" in p["body"] for p in agent.posts_in("room-family"))
