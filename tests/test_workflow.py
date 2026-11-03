from family_room import workflow, writers
from family_room.config import load_chat
from family_room.detect import analyze
from nightguard.family import apply_rules


def event_for(chat_id):
    chat = load_chat(chat_id)
    return apply_rules(analyze(chat), app=chat["app"], contact=chat["contact"])


def test_shared_event_carries_only_flagged_phrases():
    e = event_for("snap-secret")
    assert e["shared"] and e["severity"] == "high"
    assert [s["id"] for s in e["signals"]] == ["secrecy"]  # flattery and platform_move stay with the child
    assert e["signals"][0]["quote"] == "don't tell your parents ok?"
    assert "messages" not in e


def test_child_decides_when_rules_say_so():
    e = event_for("whatsapp-number")
    assert e["severity"] == "medium" and not e["shared"]


def test_nothing_risky_makes_no_event():
    assert event_for("just-gaming") is None


def test_plan_follows_night_guard_steps():
    keys = [s.key for s in workflow.plan_for(event_for("snap-secret"), "Lia")]
    assert keys == ["tell_child", "talk", "evidence", "report"]
    keys = [s.key for s in workflow.plan_for(event_for("gift-card-threat"), "Lia")]
    assert "hotline" in keys  # threats or money demands: SaferNet / NCMEC and the police
    keys = [s.key for s in workflow.plan_for(event_for("photo-pressure"), "Lia")]
    assert "hotline" in keys


def test_parse_commands():
    p = workflow.parse
    assert p("@family-helper approve").verb == "approve" and p("@family-helper approve").numbers == []
    assert p("approve 1 3").numbers == [1, 3]
    assert p("ok").verb == "approve"
    c = p("@family-helper edit 2: she's 10, keep it short")
    assert (c.verb, c.numbers, c.note) == ("edit", [2], "she's 10, keep it short")
    assert p("skip 4").numbers == [4]
    assert p("thanks, talking to her now") is None
    assert p("edit please").verb == "help"


def test_nothing_happens_before_approval_and_edits_are_kept():
    case = workflow.new_case(event_for("snap-secret"), "Lia")
    assert all(s.status == "proposed" for s in case.steps)
    todo, _ = workflow.apply(case, workflow.parse("approve 1 3"), "mom")
    assert [s.key for s in todo] == ["tell_child", "evidence"]
    todo, _ = workflow.apply(case, workflow.parse("edit 2: say we love her"), "dad")
    assert todo[0].key == "talk" and todo[0].note == "say we love her" and todo[0].status == "approved"
    todo, _ = workflow.apply(case, workflow.parse("skip 4"), "mom")
    assert case.steps[3].status == "skipped" and not todo
    workflow.apply(case, workflow.parse("done 3"), "mom")
    assert case.steps[2].status == "done"
    note = workflow.case_note(case)
    assert "mom approved" in note and "dad edited step 2" in note and "never the full chat" in note


def test_bad_step_number():
    case = workflow.new_case(event_for("snap-secret"), "Lia")
    todo, reply = workflow.apply(case, workflow.parse("approve 9"), "mom")
    assert not todo and "no step 9" in reply


def test_templates_follow_house_rules():
    e = event_for("gift-card-threat")
    texts = [writers.talk_script(e, "Lia"), writers.evidence_checklist(e, "Lia"), writers.app_report(e, "Lia"),
             writers.hotline_report(e, "Lia"), writers.child_note(e, "Lia"), writers.explain(e, "Lia")]
    for t in texts:
        assert "—" not in t  # no em dashes
        assert "punish" not in t.lower() or "without punishment" in t.lower() or "no punishment" in t.lower()
    assert "Don't pay" in writers.hotline_report(e, "Lia")
    assert "report.cybertip.org" in writers.hotline_report(e, "Lia")
    assert "NOT in trouble" in writers.child_note(e, "Lia")
    assert "don't screenshot or save those images" in writers.evidence_checklist(e, "Lia")


def test_case_round_trips():
    case = workflow.new_case(event_for("snap-secret"), "Lia")
    workflow.apply(case, workflow.parse("approve"), "mom")
    again = workflow.Case.from_dict(case.to_dict())
    assert again == case
