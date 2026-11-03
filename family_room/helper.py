"""family-helper: the agent that works a Night Guard alert with the parents, inside the family room.

    python -m family_room.helper

It listens to the family room through Switch. When night-guard posts an alert it loads the
alert document, explains the risk in plain words and proposes numbered steps. Only a parent
can approve; nothing is written or sent before that. Then it carries out the approved steps:
writes each one as a room document, posts it in the thread, sends the child their note in
the child's own room, and keeps a case note up to date.
"""

from __future__ import annotations

import json
import logging
import re

from . import workflow, writers
from .config import DEVICE_AGENT, HELPER_AGENT, ROOT, load_state
from .switch_client import Agent

log = logging.getLogger("family-helper")
ALERT_RE = re.compile(r"room document alert-(\w+)")
CASES_FILE = ROOT / ".cases.json"


class FamilyHelper:
    def __init__(self, agent: Agent, state: dict, cases_file=CASES_FILE):
        self.agent = agent
        self.family = state["rooms"]["family"]["id"]
        self.child_room = state["rooms"]["child"]["id"]
        self.parents = [p.lower() for p in state["parents"]]
        self.cases_file = cases_file
        self.cases: dict[str, workflow.Case] = {}
        if cases_file and cases_file.exists():
            self.cases = {k: workflow.Case.from_dict(v) for k, v in json.loads(cases_file.read_text("utf-8")).items()}

    # ── who is talking ─────────────────────────────────────────────────────
    def parent_name(self, payload: dict) -> str | None:
        """The parent's name if a parent sent this, else None (the child and other agents can't approve)."""
        names = {(payload.get("sender_name") or "").lower(), (payload.get("sender") or "").lower()}
        for parent in self.parents:
            if any(n == parent or n.startswith(f"@{parent}:") or f"-{parent}:" in n or n.split(" ")[0] == parent
                   for n in names if n):
                return parent
        return None

    def save(self) -> None:
        if self.cases_file:
            self.cases_file.write_text(json.dumps({k: c.to_dict() for k, c in self.cases.items()}, indent=2), "utf-8")

    # ── events ─────────────────────────────────────────────────────────────
    def handle(self, event: dict) -> None:
        if event.get("type") != "message" or event.get("room_id") != self.family:
            return
        p = event["payload"]
        sender = (p.get("sender_name") or "").lower()
        if sender == HELPER_AGENT:
            return
        body = p.get("body") or ""
        alert = ALERT_RE.search(body)
        if alert and sender == DEVICE_AGENT:
            self.on_alert(p, alert.group(1))
            return
        case = next((c for c in self.cases.values() if c.thread_id and c.thread_id == p.get("thread_id")), None)
        cmd = workflow.parse(body)
        if case is None or cmd is None:
            return
        parent = self.parent_name(p)
        if parent is None:
            self.agent.post(self.family, "Only a parent can decide the steps of a case.", thread_id=case.thread_id)
            return
        self.on_command(case, cmd, parent)

    def on_alert(self, payload: dict, alert_id: str) -> None:
        if alert_id in self.cases:
            return
        doc_id = self.agent.find_document(self.family, f"alert-{alert_id}")
        if doc_id is None:
            log.warning("alert %s has no document in the room", alert_id)
            return
        doc = self.agent.load_documents(self.family, [doc_id])[0]
        record = json.loads(doc["content"])
        child = record.pop("child", "your child")
        case = workflow.new_case(record, child)
        case.thread_id = payload["message_id"]
        self.cases[case.id] = case
        explanation = writers.explain(record, child)
        self.agent.mention(
            self.family,
            f"What this means: {explanation}\n\n"
            f"Here's what I suggest. I'll prepare each step only after one of you approves it:\n"
            f"{workflow.plan_text(case)}\n\n{workflow.HELP}",
            self.parents,
            thread_id=case.thread_id,
        )
        case.note_document_id = self.agent.create_document(
            self.family, f"case-{case.id}", f"Case note for alert {case.id}", workflow.case_note(case),
            instructions="Running record of the family's decisions on this Night Guard alert.")
        self.save()

    def on_command(self, case: workflow.Case, cmd: workflow.Command, parent: str) -> None:
        todo, reply = workflow.apply(case, cmd, parent)
        self.agent.post(self.family, reply, thread_id=case.thread_id)
        for step in todo:
            self.carry_out(case, step)
        self.agent.update_document(self.family, case.note_document_id, workflow.case_note(case))
        self.save()

    def carry_out(self, case: workflow.Case, step: workflow.Step) -> None:
        number = case.steps.index(step) + 1
        write = workflow.STEP_CATALOG[step.key][2]
        text = write(case.event, case.child, step.note)
        name = f"case-{case.id}-step{number}-{step.key}"
        if step.document_id:
            self.agent.update_document(self.family, step.document_id, text)
        else:
            step.document_id = self.agent.create_document(self.family, name, f"{step.output} (case {case.id})", text)
        if step.key == "tell_child":
            self.agent.post(self.child_room, text)
            step.status = "done"
            case.log.append(f"Sent {case.child} the note in their Night Guard room.")
            self.agent.post(self.family, f"✅ Step {number}: sent to {case.child} in their own room:\n> "
                            + text.replace("\n", "\n> "), thread_id=case.thread_id)
            return
        self.agent.post(self.family, f"📄 Step {number}, {step.output} (saved as room document `{name}`):\n\n{text}",
                        thread_id=case.thread_id)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(message)s")
    state = load_state()
    me = state["agents"][HELPER_AGENT]
    agent = Agent(state["switch_url"], me["id"], me["api_key"], HELPER_AGENT)
    helper = FamilyHelper(agent, state)
    log.info("family-helper listening in the family room (writer: %s)", writers.writer())
    agent.listen(helper.handle, client="family-helper")


if __name__ == "__main__":
    main()
