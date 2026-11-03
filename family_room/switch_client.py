"""A small client for the Switch agent protocol.

Down: one server-sent event stream. Up: HTTP operations. A heartbeat every 2 seconds keeps
the connection alive (https://docs.switchagents.ai/flintai/switch/internals/agent-protocol).
"""

from __future__ import annotations

import json
import logging
import threading
import time
import uuid
from collections.abc import Callable, Iterator

import httpx

log = logging.getLogger(__name__)


class SwitchError(RuntimeError):
    pass


def register_agent(base_url: str, registration_token: str, name: str, description: str) -> dict:
    """Register (or re-register) a custom always-on agent. Returns {id, api_key}; the key is shown once."""
    r = httpx.post(
        f"{base_url}/agents",
        headers={"Authorization": f"Bearer {registration_token}"},
        json={
            "name": name,
            "description": description,
            "connector_type": "custom",
            "overwrite": True,
            "integration_profile": {
                "connection_model": "always_on",
                "message_exchange": True,
                "pre_invocation_mediation": [],
                "post_invocation_mediation": [],
                "event_reporting": [],
            },
        },
        timeout=30,
    )
    if r.status_code != 200:
        raise SwitchError(f"register {name}: {r.status_code} {r.text}")
    body = r.json()
    return {"id": body["id"], "api_key": body["api_key"]}


def parse_sse(lines: Iterator[str]) -> Iterator[dict]:
    """Turn SSE lines into event dicts. Comments (keepalives) are skipped.

    An event ends at a blank line, but some HTTP clients drop blank lines, so a data payload
    is also emitted as soon as it is complete JSON (Switch sends one JSON object per event).
    """
    data: list[str] = []
    name = ""
    for line in lines:
        line = line.rstrip("\r\n")
        if line.startswith(":"):
            continue
        if line.startswith("event:"):
            name = line[6:].strip()  # control frames name themselves here, not in the JSON
            continue
        if line.startswith("data:"):
            data.append(line[5:].strip())
            try:
                event = json.loads("\n".join(data))
            except ValueError:
                continue  # a payload split over several data lines: wait for the rest
            data = []
            if isinstance(event, dict) and name and "type" not in event:
                event["type"] = name
            name = ""
            yield event
            continue
        if line == "" and data:
            log.warning("skipping a frame that is not JSON")
            data = []


class Agent:
    """One Switch agent: operations, the event stream and the heartbeat."""

    def __init__(self, base_url: str, agent_id: str, api_key: str, name: str = "", http: httpx.Client | None = None):
        self.base_url = base_url.rstrip("/")
        self.id = agent_id
        self.name = name
        self.connection_id = str(uuid.uuid4())
        self._http = http or httpx.Client(timeout=60)
        self._headers = {"Authorization": f"Bearer {api_key}"}
        self._lock = threading.RLock()  # one operation at a time: connect_to_room changes the active room
        self._room: str | None = None
        self._stop = threading.Event()
        self._ready = threading.Event()
        self.last_error = ""
        self.cursor: int | None = None

    # ── operations ──────────────────────────────────────────────────────────
    def op(self, operation: str, /, **args) -> object:
        with self._lock:
            r = self._http.post(
                f"{self.base_url}/agents/{self.id}/ops/{operation}",
                headers={**self._headers, "X-Switch-Connection-Id": self.connection_id},
                json=args,
            )
            if r.status_code != 200:
                raise SwitchError(f"{operation} failed {r.status_code}: {r.text[:300]}")
            return r.json()["result"]

    def in_room(self, room_id: str) -> None:
        """Make room_id the active room for the operations that follow."""
        with self._lock:
            if self._room != room_id:
                self.op("connect_to_room", room_id=room_id, include_general_instructions=False)
                self._room = room_id

    def post(self, room_id: str, body: str, thread_id: str | None = None) -> str:
        with self._lock:
            self.in_room(room_id)
            return self.op("post_message", body=body, thread_id=thread_id)["event_id"]

    def mention(self, room_id: str, body: str, names: list[str], thread_id: str | None = None) -> object:
        with self._lock:
            self.in_room(room_id)
            return self.op("send_targeted_message", body=body, target_names=names, thread_id=thread_id)

    def create_document(self, room_id: str, name: str, description: str, content: str, instructions: str = "") -> str:
        with self._lock:
            self.in_room(room_id)
            return self.op("create_room_document", name=name, description=description,
                           instructions=instructions or description, content=content)["document_id"]

    def update_document(self, room_id: str, document_id: str, content: str) -> None:
        with self._lock:
            self.in_room(room_id)
            self.op("update_room_document", document_id=document_id, content=content)

    def find_document(self, room_id: str, name: str) -> str | None:
        """The id of the room document called `name`, from the room's context."""
        with self._lock:
            context = self.op("connect_to_room", room_id=room_id, include_general_instructions=False)
            self._room = room_id
        return next((d["id"] for d in context.get("documents", []) if d.get("name") == name), None)

    def load_documents(self, room_id: str, ids: list[str]) -> list[dict]:
        with self._lock:
            self.in_room(room_id)
            return self.op("load_internal_documents", ids=ids)

    # ── stream and heartbeat ────────────────────────────────────────────────
    def _beat_forever(self) -> None:
        with httpx.Client(timeout=10) as http:
            while not self._stop.wait(2):
                try:
                    body = {"connection_id": self.connection_id}
                    if self.cursor is not None:
                        body["cursor"] = self.cursor
                    http.post(f"{self.base_url}/agents/{self.id}/connection/beat", headers=self._headers, json=body)
                except httpx.HTTPError:
                    pass  # the stream loop reconnects; a missed beat is not fatal within the 6 s TTL

    def _stream_forever(self, handle: Callable[[dict], None] | None, client: str) -> None:
        while not self._stop.is_set():
            url = (f"{self.base_url}/agents/{self.id}/events?connection_id={self.connection_id}"
                   f"&scope=all&filter=all&start_from=head&client={client}")
            headers = {**self._headers, "Accept": "text/event-stream"}
            if self.cursor is not None:
                headers["Last-Event-ID"] = str(self.cursor)
            try:
                with httpx.stream("GET", url, headers=headers, timeout=httpx.Timeout(10, read=None)) as r:
                    if r.status_code != 200:
                        raise SwitchError(f"stream {r.status_code}: {r.read()[:200]!r}")
                    for event in parse_sse(r.iter_lines()):
                        if self._stop.is_set():
                            return
                        if event.get("type") == "connection_state":
                            self._room = None  # a new connection holds no room yet
                            self._ready.set()
                        if isinstance(event.get("sequence"), int):
                            self.cursor = event["sequence"]
                        if handle is None:
                            continue
                        try:
                            handle(event)
                        except Exception:  # noqa: BLE001  one bad event must not stop the family's agent
                            log.exception("handler failed")
            except Exception as exc:  # noqa: BLE001  keep the connection alive whatever happened
                if self._stop.is_set():
                    return
                self.last_error = f"{type(exc).__name__}: {exc}"
                log.warning("stream dropped (%s), reconnecting", exc)
                time.sleep(2)

    def connect(self, handle: Callable[[dict], None] | None = None, client: str = "night-guard-switch",
                timeout: float = 30) -> Agent:
        """Open the event stream (operations need a live connection) and start the heartbeat."""
        self._stop.clear()
        self._ready.clear()
        threading.Thread(target=self._stream_forever, args=(handle, client), daemon=True).start()
        threading.Thread(target=self._beat_forever, daemon=True).start()
        if not self._ready.wait(timeout):
            raise SwitchError(f"the event stream did not open ({self.last_error or 'no frame received'})")
        return self

    def listen(self, handle: Callable[[dict], None], client: str = "night-guard-switch") -> None:
        """Deliver every event in the agent's rooms to handle(), until stopped."""
        self.connect(handle, client)
        while not self._stop.wait(1):
            pass

    def stop(self) -> None:
        self._stop.set()

    def __enter__(self) -> Agent:
        return self.connect()

    def __exit__(self, *exc) -> None:
        self.stop()
