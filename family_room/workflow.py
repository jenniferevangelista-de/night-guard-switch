"""The family's case: plan, the parents' decisions, and the case note. No network here.

An alert becomes a case. family-helper proposes numbered steps; a parent answers in the
alert's thread and nothing is written or sent before that answer:

  approve            every proposed step
  approve 1 3        only those steps
  edit 2: <note>     change a step (approves it with the parent's note)
  skip 4             leave a step out
  done 1             mark a step as done after doing it
  status             show where the case stands
"""

from __future__ import annotations

import re
import time
from dataclasses import asdict, dataclass, field

from . import writers

STEP_CATALOG = {
    "talk": ("Talk with {child} today, calmly and without punishment", "talk script", writers.talk_script),
    "evidence": ("Keep the evidence before blocking", "evidence checklist", writers.evidence_checklist),
    "report": ("Block and report {contact} on {app}", "report text for {app}", writers.app_report),
    "hotline": ("Report to SaferNet / NCMEC and the police. Don't pay", "hotline report guide", writers.hotline_report),
    "tell_child": ("Send {child} a calm note now: not in trouble, talk today", "note to {child}", writers.child_note),
}


@dataclass
class Step:
    key: str
    title: str
    output: str
    status: str = "proposed"  # proposed, approved, skipped, done
    note: str = ""
    document_id: str = ""


@dataclass
class Case:
    id: str
    event: dict
    child: str
    thread_id: str = ""
    steps: list[Step] = field(default_factory=list)
    log: list[str] = field(default_factory=list)
    note_document_id: str = ""

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> Case:
        return cls(**{**d, "steps": [Step(**s) for s in d.get("steps", [])]})


def plan_for(event: dict, child: str) -> list[Step]:
    """Night Guard's 'what to do now' for the family, turned into steps the agent can carry out."""
    ids = writers.signal_ids(event)
    keys = ["tell_child", "talk", "evidence"]
    if event["severity"] in ("high", "medium"):
        keys.append("report")
    if ids & writers.HOTLINE_SIGNALS:
        keys.append("hotline")
    fmt = {"child": child, "contact": event["contact"], "app": event["app"]}
    return [Step(k, STEP_CATALOG[k][0].format(**fmt), STEP_CATALOG[k][1].format(**fmt)) for k in keys]


def new_case(event: dict, child: str) -> Case:
    case = Case(id=event["id"], event=event, child=child, steps=plan_for(event, child))
    case.log.append(f"{event['time']} Night Guard shared a {event['severity']} alert from {event['app']}.")
    return case


# ── commands ────────────────────────────────────────────────────────────────
@dataclass
class Command:
    verb: str  # approve, skip, edit, done, status, help
    numbers: list[int] = field(default_factory=list)
    note: str = ""


_MENTION = re.compile(r"@[\w.-]+")


def parse(text: str) -> Command | None:
    """Read a parent's reply. Returns None when it isn't a command (just conversation)."""
    t = _MENTION.sub("", text or "").strip()
    m = re.match(r"(?is)^(approve|ok|yes|skip|edit|done|status|help)\b\s*(.*)$", t)
    if not m:
        return None
    verb = {"ok": "approve", "yes": "approve"}.get(m.group(1).lower(), m.group(1).lower())
    rest = m.group(2).strip()
    if verb == "edit":
        em = re.match(r"(?s)^(\d+)\s*[:\-]?\s*(.+)$", rest)
        if not em:
            return Command("help")
        return Command("edit", [int(em.group(1))], em.group(2).strip())
    nums = [int(n) for n in re.findall(r"\d+", rest.split(":")[0])] if verb in ("approve", "skip", "done") else []
    if verb in ("approve", "skip") and re.match(r"(?i)^all\b", rest):
        nums = []
    return Command(verb, nums)


def _stamp() -> str:
    return time.strftime("%Y-%m-%d %H:%M")


def apply(case: Case, cmd: Command, by: str) -> tuple[list[Step], str]:
    """Apply a parent's command. Returns (steps to carry out now, short reply for the thread)."""
    n = len(case.steps)
    bad = [x for x in cmd.numbers if not 1 <= x <= n]
    if bad:
        return [], f"There is no step {bad[0]}. Steps go from 1 to {n}."
    pick = [case.steps[i - 1] for i in cmd.numbers] if cmd.numbers else list(case.steps)
    if cmd.verb == "approve":
        todo = [s for s in pick if s.status == "proposed"]
        for s in todo:
            s.status = "approved"
        case.log.append(f"{_stamp()} {by} approved: {', '.join(s.title for s in todo) or 'nothing new'}.")
        return todo, f"Approved by {by}. Working on {len(todo)} step(s) now." if todo else "Those steps were already decided."
    if cmd.verb == "skip":
        for s in pick:
            if s.status == "proposed":
                s.status = "skipped"
        case.log.append(f"{_stamp()} {by} skipped: {', '.join(s.title for s in pick)}.")
        return [], f"Skipped by {by}."
    if cmd.verb == "edit":
        s = pick[0]
        s.note = cmd.note
        already = s.status in ("approved", "done")
        if s.status in ("proposed", "skipped"):
            s.status = "approved"
        case.log.append(f"{_stamp()} {by} edited step {cmd.numbers[0]}: {cmd.note}")
        return [s], f"Got it, {by}. {'Rewriting' if already else 'Writing'} step {cmd.numbers[0]} with your note."
    if cmd.verb == "done":
        for s in pick:
            if s.status == "approved":
                s.status = "done"
        case.log.append(f"{_stamp()} {by} marked done: {', '.join(s.title for s in pick)}.")
        return [], f"Marked done by {by}. " + status_line(case)
    if cmd.verb == "status":
        return [], status_text(case)
    return [], HELP


HELP = ("Reply in this thread: `approve` (all steps), `approve 1 3`, `edit 2: <your change>`, "
        "`skip 4`, `done 1`, `status`. Nothing is written or sent before a parent approves.")

ICON = {"proposed": "⏳", "approved": "▶️", "skipped": "⏭️", "done": "✅"}


def plan_text(case: Case) -> str:
    lines = [f"{i}. {s.title} → I'll write the {s.output}" for i, s in enumerate(case.steps, 1)]
    return "\n".join(lines)


def status_line(case: Case) -> str:
    counts = {k: sum(s.status == k for s in case.steps) for k in ICON}
    return f"{counts['done']} done, {counts['approved']} in progress, {counts['proposed']} waiting, {counts['skipped']} skipped."


def status_text(case: Case) -> str:
    rows = [f"{ICON[s.status]} {i}. {s.title} ({s.status})" for i, s in enumerate(case.steps, 1)]
    return "Case status\n" + "\n".join(rows) + "\n" + status_line(case)


def case_note(case: Case) -> str:
    e = case.event
    sig = "\n".join(f"- {s['label']}: \"{s['quote']}\"" for s in e["signals"])
    steps = "\n".join(f"{ICON[s.status]} {s.title} ({s.status})" + (f", note: {s.note}" if s.note else "")
                      for s in case.steps)
    return (
        f"Case {case.id}: {e['severity']} risk on {e['app']}, contact {e['contact']}\n\n"
        f"What Night Guard shared (never the full chat):\n{sig}\n\n"
        f"Steps:\n{steps}\n\n"
        "Timeline:\n" + "\n".join(f"- {line}" for line in case.log)
    )
