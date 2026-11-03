# How the Night Guard Family Room videos were made

Two videos, in the same format as the [Night Guard videos](https://github.com/jenniferevangelista-de/night-guard/blob/main/docs/VIDEOS.md): Jennifer opens them, and the narrator of the Night Guard films (Snoozy) tells the rest. Every chat shown is fictional.

| Video | What it is |
|---|---|
| **Film** | Paper-style animation. The Night Guard story (the problem, the guard, the kid's warning, the family alert), then what is new: the alert lands in the family's group chat through Switch, family-helper explains and proposes steps, the parents decide, the kid is told, threats get SaferNet / NCMEC and "don't pay", and what runs under the hood |
| **Tour** | A real recording of this repository running: Switch v0.31.0, Mattermost, both agents and Gemma, in a paper frame with the narrator beside it, a title for each part and subtitles |

Both are recorded and rendered in the cloud by the [videos workflow](../.github/workflows/videos.yml), never on a laptop.

## Pipeline

```
FILM (Windows runner)                         TOUR (Linux runner, then Windows runner)
film_script.py   narration + timeline         tour_script.py   narration, one line per part
       |                                             |
film.py          every scene, drawn frame     record_demo.py   Switch + Mattermost + agents for real,
       |         by frame (Pillow)                   |         Playwright films mom's view; Lia's view
film_audio.py    voices + drama bed +                |         is a real screenshot of her own session
       |         Funkorama + effects          tour_build.py    paper frame, narrator, titles, subtitles,
film_render.py   frames -> ffmpeg -> mp4,                       waits for the agent cut out
                 20% faster (like Night Guard)
```

## What was reused from Night Guard, and what is new

| Reused as it was (in `video/ng/` and the scenes marked in `film.py`) | New for this project |
|---|---|
| The narrator character (`ng/ng_sloth.py`), the paper, ink and stick figures (`ng/palito.py`), the props (`ng/ng_film_helpers.py`) | Jennifer's intro (Ava voice, first person) |
| The film scenes intro, night, stat, fast, platforms, parents, guard, alert, family and peace, with the narrator's lines word for word | The scenes after, room, helper, decide, kid, threat, tech and the end card |
| The mix: original drama bed until the guard appears, then Funkorama; the app's real spoken warning (ElevenLabs, `ng/audio/`) | Sound effects for the new scenes |
| The render (frames piped to ffmpeg, -14 LUFS, 20% faster) and the tour frame (`tour_build.py`) | The tour content: a real Switch + Mattermost run, recorded by `record_demo.py` |

## Tools

| Tool | Used for |
|---|---|
| Python 3.12 + Pillow | Every frame of the film and the tour frame (1920x1080, 24 fps) |
| NumPy + soundfile | The mix and the original drama score |
| ffmpeg | Encoding, cutting the agent's waits, loudness |
| edge-tts | Voices: `en-US-BrianMultilingualNeural` (the narrator, as in every Night Guard video) and `en-US-AvaMultilingualNeural` (Jennifer) |
| Playwright + Chromium | Films the real Mattermost on the Switch server |
| Switch v0.31.0, Mattermost, Ollama + Gemma 3 4B | What the tour shows, running for real on the runner |

## Music credit

"Funkorama" by Kevin MacLeod (incompetech.com), licensed under Creative Commons: By Attribution 4.0 (https://creativecommons.org/licenses/by/4.0/). The dramatic opening music is original and generated in code.
