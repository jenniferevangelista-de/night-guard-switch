"""Run Night Guard's detector with a choice of model backend.

The prompt, schema and post-processing are Night Guard's own (nightguard/detector.py).
Only the model call is chosen here:

  replay  (default) returns the hand labels stored with each fictional chat. No model,
          no key, same result every run: this is what the tests and the end-to-end check use.
  github  GitHub Models free tier (https://models.github.ai), with a GitHub token.
  ollama  Gemma on the child's own computer, exactly like the Night Guard app.
"""

from __future__ import annotations

import json
import os

import httpx

from nightguard.detector import SCHEMA, SYSTEM, _format_chat, postprocess

GITHUB_MODELS_URL = "https://models.github.ai/inference/chat/completions"


def backend() -> str:
    return os.environ.get("NG_DETECTOR", "replay")


def _replay(chat: dict) -> dict:
    return {"signals": [dict(s) for s in chat.get("labels", [])], "summary": "Hand-labelled fictional chat."}


def _github(messages: list[dict]) -> dict | None:
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if not token:
        raise RuntimeError("NG_DETECTOR=github needs GITHUB_TOKEN (any GitHub token with models access)")
    r = httpx.post(
        GITHUB_MODELS_URL,
        headers={"Authorization": f"Bearer {token}"},
        json={
            "model": os.environ.get("NG_GITHUB_MODEL", "openai/gpt-4.1-mini"),
            "temperature": 0,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": SYSTEM + "\n\nAnswer with JSON matching: " + json.dumps(SCHEMA)},
                {"role": "user", "content": "Chat:\n" + _format_chat(messages) + "\n\nReturn the JSON."},
            ],
        },
        timeout=60,
    )
    r.raise_for_status()
    try:
        return json.loads(r.json()["choices"][0]["message"]["content"])
    except (ValueError, KeyError, IndexError):
        return None


def _ollama(messages: list[dict]) -> dict | None:
    url = os.environ.get("OLLAMA_URL", "http://localhost:11434")
    r = httpx.post(
        f"{url}/api/chat",
        json={
            "model": os.environ.get("NG_MODEL", "gemma4:e4b"),
            "stream": False,
            "format": SCHEMA,
            "think": False,
            "options": {"temperature": 0, "num_ctx": 4096},
            "messages": [
                {"role": "system", "content": SYSTEM},
                {"role": "user", "content": "Chat:\n" + _format_chat(messages) + "\n\nReturn the JSON."},
            ],
        },
        timeout=120,
    )
    r.raise_for_status()
    try:
        return json.loads(r.json()["message"]["content"])
    except ValueError:
        return None


def analyze(chat: dict, lang: str = "en") -> dict:
    """Night Guard's result for one chat: severity, signals with quotes, parent steps."""
    name = backend()
    messages = chat["messages"]
    if name == "replay":
        raw, model = _replay(chat), "replay of hand labels"
    elif name == "github":
        raw, model = _github(messages), os.environ.get("NG_GITHUB_MODEL", "openai/gpt-4.1-mini")
    elif name == "ollama":
        raw, model = _ollama(messages), os.environ.get("NG_MODEL", "gemma4:e4b")
    else:
        raise ValueError(f"unknown NG_DETECTOR {name!r} (use replay, github or ollama)")
    return postprocess(raw, messages, lang, model=model)
