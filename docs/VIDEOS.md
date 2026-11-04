# How the Night Guard Family Room videos were made

Two videos, in the same format as the [Night Guard videos](https://github.com/jenniferevangelista-de/night-guard/blob/main/docs/VIDEOS.md). Jennifer narrates both in the first person, and Snoozy, Night Guard's little guard, is on screen with her, his mouth moving with the narration. Every chat shown is fictional, and every number is real (Night Guard's evaluation and this repository's tests).

| Video | What it is |
|---|---|
| **Film** | Paper-style animation with real screenshots taped on the page. The Night Guard story (the problem, the guard, its results, the kid's warning), a BEFORE (a parent alone with one alert at night) and an AFTER, which is what is new: the alert lands in the family's group chat through Switch, family-helper explains and proposes steps, the parents decide, the kid is told, threats get SaferNet / NCMEC and "don't pay", a before/after side by side, and the proof: 13 end-to-end checks on a real Switch on every push |
| **Tour** | A real recording of this repository running: Switch v0.31.0, Mattermost, both agents and Gemma, in a paper frame with Snoozy beside it, a title for each part and subtitles |

Both are recorded and rendered in the cloud by the [videos workflow](../.github/workflows/videos.yml), never on a laptop.

## Pipeline

```
FILM (Windows runner)                         TOUR (Linux runner, then Windows runner)
film_script.py   narration + timeline         tour_script.py   narration, one line per part
       |                                             |
film.py          every scene, drawn frame     record_demo.py   Switch + Mattermost + agents for real,
       |         by frame (Pillow)                   |         Playwright films mom's view; Lia's view
film_audio.py    voices + drama bed +                |         is a real screenshot of her own session
       |         Funkorama + effects          tour_build.py    paper frame, Snoozy, titles, subtitles,
film_render.py   frames -> ffmpeg -> mp4,                       waits for the agent cut out
                 20% faster (like Night Guard)
```

## What was reused from Night Guard, and what is new

| Reused as it was (in `video/ng/` and the scenes marked in `film.py`) | New for this project |
|---|---|
| Snoozy (`ng/ng_sloth.py`), the paper, ink and stick figures (`ng/palito.py`), the props (`ng/ng_film_helpers.py`) | Jennifer's intro (Ava voice, first person) |
| The film scenes night, stat, fast and alert, with their lines word for word, and the paper style | Jennifer's narration; the scenes hello, guard, results, before, room, helper, decide, kid, threat, before/after, proof and end; the real screenshots in `ng/shots/` |
| The mix: original drama bed until the guard appears, then Funkorama (30%); the app's real spoken warning (ElevenLabs, `ng/audio/`) | Tonal sound effects only (sweep, tick, pop, chime; no noise) |
| The render (frames piped to ffmpeg, -14 LUFS, 20% faster) and the tour frame (`tour_build.py`) | The tour content: a real Switch + Mattermost run, recorded by `record_demo.py` |

## Tools

| Tool | Used for |
|---|---|
| Python 3.12 + Pillow | Every frame of the film and the tour frame (1920x1080, 24 fps) |
| NumPy + soundfile | The mix and the original drama score |
| ffmpeg | Encoding, cutting the agent's waits, loudness |
| edge-tts | Jennifer's voice: `en-US-AvaMultilingualNeural` |
| Playwright + Chromium | Films the real Mattermost on the Switch server |
| Switch v0.31.0, Mattermost, Ollama + Gemma 3 4B | What the tour shows, running for real on the runner |

## Music credit

"Funkorama" by Kevin MacLeod (incompetech.com), licensed under Creative Commons: By Attribution 4.0 (https://creativecommons.org/licenses/by/4.0/). The dramatic opening music is original and generated in code.
