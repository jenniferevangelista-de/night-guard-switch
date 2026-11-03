"""One-time setup on a local Switch (with its bundled Mattermost).

    SWITCH_ENV=../switch/.env python -m family_room.setup

Creates the fictional family in Mattermost (mom, dad and Lia), registers the two agents
in Switch, and creates two Switch rooms:
  family-safety    mom, dad, night-guard, family-helper   (alerts and decisions)
  lia-night-guard  Lia, night-guard, family-helper         (what the child is told)
Everything is saved in .state.json (git-ignored). Safe to run again.
"""

from __future__ import annotations

import os
import secrets
import time
from pathlib import Path

import httpx

from .config import DEVICE_AGENT, HELPER_AGENT, STATE_FILE, load_state, save_state
from .switch_client import Agent, SwitchError, register_agent

SWITCH = os.environ.get("SWITCH_URL", "http://localhost:8000")
MM = os.environ.get("MATTERMOST_URL", "http://localhost:8065")
PARENTS = ["mom", "dad"]
CHILD = {"name": "Lia", "username": "lia"}
ROOMS = {
    "family": ("family-safety", "Night Guard alerts for the family. Only the flagged phrase is shared, never the chat.",
               PARENTS),
    "child": ("lia-night-guard", "Lia's own room: Night Guard tells her when something is shared with the family.",
              [CHILD["username"]]),
}
AGENTS = {
    DEVICE_AGENT: "Night Guard on the child's computer. Shares only risk type, app, contact and flagged phrase.",
    HELPER_AGENT: "Explains Night Guard alerts to parents, proposes next steps and carries them out once a parent approves.",
}


def read_env(path: Path) -> dict[str, str]:
    values = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.lstrip().startswith("#"):
            k, _, v = line.partition("=")
            values[k.strip()] = v.strip().strip('"')
    return values


class Mattermost:
    def __init__(self, url: str, login: str, password: str):
        self.url = url
        self.http = httpx.Client(timeout=30)
        r = self.http.post(f"{url}/api/v4/users/login", json={"login_id": login, "password": password})
        r.raise_for_status()
        self.http.headers["Authorization"] = f"Bearer {r.headers['Token']}"

    def get(self, path: str) -> httpx.Response:
        return self.http.get(f"{self.url}/api/v4{path}")

    def post(self, path: str, json: dict) -> httpx.Response:
        return self.http.post(f"{self.url}/api/v4{path}", json=json)

    def ensure_user(self, username: str, password: str, team_id: str, first_name: str) -> str:
        r = self.get(f"/users/username/{username}")
        if r.status_code == 200:
            uid = r.json()["id"]
            self.http.put(f"{self.url}/api/v4/users/{uid}/password", json={"new_password": password})
        else:
            r = self.post("/users", {"username": username, "email": f"{username}@family.example.test",
                                     "password": password, "first_name": first_name})
            r.raise_for_status()
            uid = r.json()["id"]
        self.post(f"/teams/{team_id}/members", {"team_id": team_id, "user_id": uid})
        return uid

    def channel_id(self, team_id: str, name: str) -> str:
        for _ in range(30):
            r = self.get(f"/teams/{team_id}/channels/name/{name}")
            if r.status_code == 200:
                return r.json()["id"]
            time.sleep(1)
        raise RuntimeError(f"no Mattermost channel {name}")


def main() -> None:
    env = read_env(Path(os.environ.get("SWITCH_ENV", "../switch/.env")))
    previous = load_state() if STATE_FILE.exists() else {}
    passwords = previous.get("passwords", {})
    mm = Mattermost(MM, env["MATTERMOST_ADMIN_USER"], env["MATTERMOST_ADMIN_PASSWORD"])
    team_id = mm.get(f"/teams/name/{env['MATTERMOST_TEAM_NAME']}").json()["id"]
    users = {}
    for username, first in [("mom", "Mom"), ("dad", "Dad"), (CHILD["username"], CHILD["name"])]:
        passwords.setdefault(username, "Fam-" + secrets.token_hex(8))
        users[username] = mm.ensure_user(username, passwords[username], team_id, first)

    agents = {name: register_agent(SWITCH, env["AGENT_REGISTRATION_TOKEN"], name, desc) for name, desc in AGENTS.items()}
    helper = Agent(SWITCH, agents[HELPER_AGENT]["id"], agents[HELPER_AGENT]["api_key"], HELPER_AGENT)
    for a in agents.values():
        helper.op("update_agent_detail", agent_id=a["id"], addressing="anyone")
    bridges = helper.op("list_bridges")
    bridges = bridges if isinstance(bridges, list) else bridges.get("bridges", [])
    bridge_id = next(b["id"] for b in bridges if b["type"] == "mattermost")

    rooms = {}
    existing = {r["name"]: r for r in _rooms(helper)}
    for key, (name, description, people) in ROOMS.items():
        if name in existing:
            room_id = existing[name]["room_id"]
        else:
            room_id = helper.op("create_room", name=name, description=description,
                                agent_names=[DEVICE_AGENT, HELPER_AGENT], bridge_id=bridge_id,
                                channel_type="channel_private", instructions=description)["id"]
        channel = mm.channel_id(team_id, name)
        for username in people:
            mm.post(f"/channels/{channel}/members", {"user_id": users[username]})
        rooms[key] = {"id": room_id, "channel_id": channel, "name": name}
    try:
        helper.op("link_rooms", source_room_id=rooms["family"]["id"], target_room_id=rooms["child"]["id"],
                  label="Lia's own Night Guard room")
    except SwitchError as exc:  # linking is a convenience, not required for the workflow
        print(f"link_rooms skipped: {exc}")

    save_state({
        "switch_url": SWITCH, "mattermost_url": MM, "team": env["MATTERMOST_TEAM_NAME"],
        "agents": agents, "rooms": rooms, "parents": PARENTS, "child": CHILD, "passwords": passwords,
        "family_rules": previous.get("family_rules", {}),
    })
    print(f"Ready. Rooms: {', '.join(r['name'] for r in rooms.values())}. State in {STATE_FILE.name}.")


def _rooms(agent: Agent) -> list[dict]:
    result = agent.op("list_rooms")
    return result if isinstance(result, list) else result.get("rooms", [])


if __name__ == "__main__":
    main()
