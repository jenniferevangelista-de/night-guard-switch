"""Record the demo on a running Switch + Mattermost: the real UI, the real agents.

    python video/record_demo.py      (after scripts/demo.sh set things up and family-helper is running)

Playwright drives Chrome signed in to Mattermost as mom; mom's reply is typed into the real
thread composer, dad's edit is posted through the API and shows up live. A caption bar is
drawn over the page. Each scene lasts at least as long as its narration line, and the scene
start times go to video/work/scenes.json so the narration can be laid on top afterwards.
"""

from __future__ import annotations

import base64
import json
import re
import subprocess
import sys
import time
from pathlib import Path

from playwright.sync_api import Page, sync_playwright

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from family_room.config import load_state  # noqa: E402
from family_room.setup import Mattermost  # noqa: E402

WORK = ROOT / "video" / "work"
W, H = 1440, 810  # recorded at this size and scaled to 1080p, so the chat text is easy to read

CSS = """
#ng-cap{pointer-events:none;position:fixed;left:0;right:0;top:0;z-index:2147483647;background:rgba(15,23,42,.95);color:#fff;
 font:600 28px/1.35 Helvetica,Arial,sans-serif;padding:18px 40px 22px;box-shadow:0 4px 20px rgba(0,0,0,.3)}
#ng-cap small{display:block;font-weight:400;font-size:21px;color:#cbd5e1;margin-top:6px}
#ng-badge{pointer-events:none;position:fixed;bottom:250px;left:18px;z-index:2147483647;background:#4338ca;color:#fff;
 font:700 20px Helvetica,Arial,sans-serif;padding:8px 16px;border-radius:999px}
#ng-card{position:fixed;inset:0;z-index:2147483647;background:linear-gradient(135deg,#0b1026,#312e81);color:#fff;
 display:none;flex-direction:column;justify-content:center;padding:0 140px;font-family:Helvetica,Arial,sans-serif}
#ng-card h1{font-size:72px;margin:0 0 22px} #ng-card p{font-size:32px;color:#c7d2fe;margin:8px 0;line-height:1.4}
#ng-card .tag{font-size:22px;font-weight:700;background:#fbbf24;color:#1f2937;padding:6px 14px;border-radius:999px;
 width:max-content;margin-bottom:26px}
#ng-pic{position:fixed;inset:0;z-index:2147483646;background:linear-gradient(135deg,#0b1026,#312e81);display:none;
 align-items:center;justify-content:center;padding-top:60px}
#ng-pic img{max-width:86%;max-height:78%;border-radius:14px;box-shadow:0 20px 60px rgba(0,0,0,.5);border:3px solid #fbbf24}
.announcement-bar{display:none!important}
"""
OVERLAY = """(css) => { if (document.getElementById('ng-cap')) return;
 const s=document.createElement('style'); s.textContent=css; document.head.appendChild(s);
 for (const id of ['ng-cap','ng-badge','ng-card','ng-pic']) { const d=document.createElement('div'); d.id=id;
   d.style.display='none'; document.body.appendChild(d); } }"""


class Director:
    def __init__(self, page: Page, voice: dict[str, float], t0: float):
        self.page, self.voice = page, voice
        self.t0 = t0  # when the recording started, so scene times match the video
        self.scenes: list[dict] = []
        self.caption = ("", "")
        self.badge = ""

    def overlay(self) -> None:
        self.page.evaluate(OVERLAY, CSS)
        self.set_caption(*self.caption)
        self.set_badge(self.badge)

    def set_caption(self, title: str, sub: str = "") -> None:
        self.caption = (title, sub)
        html = title + (f"<small>{sub}</small>" if sub else "")
        self.page.evaluate("([h]) => {const c=document.getElementById('ng-cap'); if(!c) return;"
                           "c.innerHTML=h; c.style.display=h?'block':'none';}", [html])

    def set_badge(self, text: str) -> None:
        self.badge = text
        self.page.evaluate("([t]) => {const b=document.getElementById('ng-badge'); if(!b) return;"
                           "b.textContent=t; b.style.display=t?'block':'none';}", [text])

    def card(self, tag: str, title: str, lines: list[str], show: bool = True) -> None:
        body = f'<span class="tag">{tag}</span><h1>{title}</h1>' + "".join(f"<p>{x}</p>" for x in lines)
        self.page.evaluate("([b, s]) => {const c=document.getElementById('ng-card'); c.innerHTML=b;"
                           "c.style.display=s?'flex':'none';}", [body, show])

    def picture(self, png: bytes | None) -> None:
        """Show a real screenshot (another person's view) full screen, or hide it."""
        src = "data:image/png;base64," + base64.b64encode(png).decode() if png else ""
        self.page.evaluate("([s]) => {const c=document.getElementById('ng-pic');"
                           "c.innerHTML=s?`<img src='${s}'>`:''; c.style.display=s?'flex':'none';}", [src])

    def scene(self, key: str, action=None, extra: float = 0.8, narrate_after: bool = False) -> None:
        """Start scene `key`, run its action, and hold until its narration has finished.

        narrate_after: the narration starts once the action is done (e.g. once Gemma's answer is on
        screen); the wait before it is cut out of the final video.
        """
        start = time.time()
        if action:
            action()
        at = time.time() if narrate_after else start
        rest = self.voice.get(key, 3) + extra - (time.time() - at)
        if rest > 0:
            self.page.wait_for_timeout(rest * 1000)
        self.scenes.append({"key": key, "start": round(start - self.t0, 2), "at": round(at - self.t0, 2),
                            "end": round(time.time() - self.t0, 2)})


def login(page: Page, mm_url: str, username: str, password: str) -> None:
    """Sign in to the local Mattermost as one of the fictional family members (test accounts from setup)."""
    page.context.clear_cookies()
    # Mattermost sets the session cookies only for browser-style (XHR) requests.
    r = page.request.post(f"{mm_url}/api/v4/users/login", data={"login_id": username, "password": password},
                          headers={"X-Requested-With": "XMLHttpRequest"})
    assert r.ok, r.text()
    if any(c["name"] == "MMAUTHTOKEN" for c in page.context.cookies()):
        return
    page.goto(f"{mm_url}/login")  # fallback: the real login form
    page.locator("#input_loginId").fill(username)
    page.locator("#input_password-input").fill(password)
    page.keyboard.press("Enter")
    page.wait_for_url(lambda url: "/login" not in url, timeout=30000)


COMPOSER = "#post_textbox, [data-testid='post_textbox']"


def open_channel(page: Page, url: str, ready: str = COMPOSER) -> None:
    """Go to a channel, getting past Mattermost's 'view in app or browser' landing page."""
    page.goto(url)
    for _ in range(60):
        if page.locator(ready).count():
            break
        landing = page.get_by_text("View in Browser", exact=False)
        if landing.count():
            landing.first.click()
        page.wait_for_timeout(1000)
    page.locator(ready).first.wait_for(timeout=30000)
    page.wait_for_timeout(1200)


def open_thread(page: Page, root_text: str) -> None:
    """Open the thread of the post containing root_text in the right-hand panel, and widen it."""
    post = page.locator("[id^='post_']", has_text=root_text).last
    button = post.get_by_role("button", name=re.compile(r"\d+ repl")).first
    button.wait_for(timeout=120000)
    button.click()
    page.locator("#rhsContainer, .sidebar--right").first.wait_for(timeout=15000)
    expand = page.locator("button[aria-label*='Expand' i]")
    if expand.count():
        expand.first.click()
    page.wait_for_timeout(800)


def scroll_thread(page: Page) -> None:
    page.mouse.move(W * 0.6, H * 0.55)
    page.mouse.wheel(0, 8000)


def wait_text(page: Page, text: str, timeout: float = 240) -> None:
    """Wait for text in Mattermost itself (#root), never in the captions drawn over it."""
    page.locator("#root").get_by_text(text, exact=False).last.wait_for(timeout=timeout * 1000)


def main() -> None:
    state = load_state()
    voice = json.loads((WORK / "voice.json").read_text())
    mm_url, team = state["mattermost_url"], state["team"]
    pw = state["passwords"]
    dad = Mattermost(mm_url, "dad", pw["dad"])
    family = state["rooms"]["family"]
    (WORK / "raw").mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(args=["--hide-scrollbars"])
        ctx = browser.new_context(viewport={"width": W, "height": H}, record_video_dir=str(WORK / "raw"),
                                  record_video_size={"width": W, "height": H})
        page = ctx.new_page()
        t0 = time.time()  # the recording starts with the page
        login(page, mm_url, "mom", pw["mom"])
        try:
            open_channel(page, f"{mm_url}/{team}/channels/{family['name']}")
        except Exception:
            page.screenshot(path=str(WORK / "fail.png"))
            print("landed on", page.url, page.title())
            raise
        d = Director(page, voice, t0)
        d.overlay()
        d.set_badge("Signed in as mom")

        d.scene("d0_title", lambda: d.card("Flip the Switch · Track 02", "Night Guard Family Room",
                                           ["A child-safety alert, worked out by the parents and an AI agent",
                                            "in the family's group chat, through Switch."]))
        d.card("", "", [], show=False)

        def alert():
            d.set_caption("1 · Night Guard spots a risk on the child's computer",
                          "Switch posts it in the family room: only the flagged phrase, never the chat")
            subprocess.run([sys.executable, "-m", "family_room.device", "snap-secret"], cwd=ROOT, check=True)
            wait_text(page, "Night Guard alert")
        d.scene("d1_alert", alert)

        def plan():
            d.set_caption("2 · family-helper explains and proposes steps",
                          "It waits: nothing is written or sent before a parent approves")
            open_thread(page, "contact Alex_17")
            wait_text(page, "Here's what I suggest")
            scroll_thread(page)
        d.scene("d2_plan", plan, narrate_after=True)

        def approve():
            d.set_caption("3 · Mom approves in the thread", "@family-helper approve 1 3 4")
            box = page.locator("#reply_textbox, [data-testid='reply_textbox']").first
            box.wait_for(timeout=15000)
            box.type("@family-helper approve 1 3 4 ", delay=60)
            page.keyboard.press("Escape")
            box.focus()
            page.keyboard.press("Enter")
        d.scene("d3_approve", approve)

        def outputs():
            d.set_caption("4 · The agent carries out the approved steps",
                          "Note to Lia, evidence checklist, report text: each saved as a Switch room document")
            wait_text(page, "report text for Roblox")
            scroll_thread(page)
        d.scene("d4_outputs", outputs)

        def edit():
            d.set_caption("5 · Dad edits a step", "edit 2: she's 10, keep it short and start by saying we love her")
            alert_post = next(p_ for p_ in reversed(_posts(dad, family["channel_id"]))
                              if "Night Guard alert" in p_["message"])
            dad.post("/posts", {"channel_id": family["channel_id"], "root_id": alert_post["id"],
                                "message": "@family-helper edit 2: she's 10, keep it short and start by saying we love her"})
            wait_text(page, "Step 2, talk script")
            scroll_thread(page)
        d.scene("d5_edit", edit, extra=2, narrate_after=True)

        def child():
            kid = browser.new_context(viewport={"width": W, "height": H}).new_page()  # Lia's own session
            login(kid, mm_url, "lia", pw["lia"])
            open_channel(kid, f"{mm_url}/{team}/channels/{state['rooms']['child']['name']}")
            kid.get_by_text("NOT in trouble", exact=False).last.wait_for(timeout=60000)
            kid.mouse.move(W * 0.5, H * 0.5)
            kid.mouse.wheel(0, 4000)
            kid.wait_for_timeout(600)
            d.set_badge("Lia's view")
            d.picture(kid.screenshot())
            d.set_caption("6 · Meanwhile, in Lia's own room", "The child is always told when something is shared")
            kid.context.close()
        d.scene("d6_child", child, extra=1.5, narrate_after=True)

        def threat():
            d.picture(None)
            d.set_badge("Signed in as mom")
            d.set_caption("7 · Threats or money demands", "SaferNet / NCMEC and the police. Don't pay. Fixed text.")
            subprocess.run([sys.executable, "-m", "family_room.device", "gift-card-threat"], cwd=ROOT, check=True)
            wait_text(page, "contact pix_trader")
            open_thread(page, "contact pix_trader")
            wait_text(page, "SaferNet / NCMEC")
            scroll_thread(page)
        d.scene("d7_threat", threat, extra=1.5, narrate_after=True)

        d.scene("d8_end", lambda: d.card("github.com/jenniferevangelista-de/night-guard-switch",
                                         "Switch is the backbone",
                                         ["2 agents · 2 linked rooms · threads · targeted messages · room documents",
                                          "scripts/demo.sh runs it all on your own Switch"]), extra=1.5)
        (WORK / "scenes.json").write_text(json.dumps(d.scenes, indent=2))
        video = page.video.path()
        ctx.close()
        browser.close()
    (WORK / "raw.json").write_text(json.dumps({"video": str(video)}))
    print("recorded", video)


def _posts(mm: Mattermost, channel: str) -> list[dict]:
    data = mm.get(f"/channels/{channel}/posts?per_page=200").json()
    return sorted((data["posts"][i] for i in data["order"]), key=lambda p: p["create_at"])


if __name__ == "__main__":
    main()
