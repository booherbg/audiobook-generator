# Build your own copy

Two audiences, two paths — pick the one that fits what you want:

1. **"I just want my own local audiobooks"** — render the books already in this repo to MP3 on
   your machine, optionally with a **different voice**. Everything you need is already here (source
   snapshots, chapter maps, recipes); you run scripts. **This page.**
2. **"I want to make a *new* audiobook from a text the repo doesn't have"** — that's the
   [authoring guide](authoring-a-new-book.md). It has two halves: a deterministic *render* half (run
   the pipeline) and a judgment-heavy *preparation* half (clean the text, chapter it, author the
   companion) where an **LLM is the recommended tool, not a nice-to-have**.

> Audio is a **build artifact** here, not a checked-in asset you're stuck with. The repo ships the
> *recipes* (`data/books/<id>.json`) and *source snapshots* (`data/sources/<id>.html`); the MP3s are
> regenerated from them. So "build your own copy" is the intended, first-class workflow — not a hack.

---

## One-time setup (macOS / Linux, ~10 min)

```sh
brew install espeak-ng ffmpeg          # Linux: apt install espeak-ng ffmpeg
uv sync --extra dev                    # Python 3.12 venv + deps (use uv; system Python is too new for the ML wheels)
uv run python -m pipeline.setup_models # fetch the Kokoro TTS model (~325 MB) into build/models/
```

No accounts, no API keys, no cloud — it all runs locally. (The model download is the only network
step; after that you can render offline.)

---

## Render a book that's already in the repo

Every book has a **recipe** in `data/books/`. One command rebuilds it end-to-end from that recipe
and the committed source snapshot — no internet, byte-stable text:

```sh
uv run audiobook regenerate rerum-novarum        # → docs/audio/rerum-novarum/<voice>/chapter-NN.mp3
```

That renders the MP3s **and** rebuilds the read-along + full-text + companion JSON. It's
**resumable** — a chapter already on disk (and plausibly complete) is skipped, so a long render
that gets interrupted just continues when you re-run it. Expect a full book to take a while (it's
CPU TTS — tens of minutes; that's normal).

**Render just the text/companion, no audio** (fast, seconds):

```sh
uv run audiobook regenerate rerum-novarum --skip-audio
```

**Listen** by opening the site locally:

```sh
uv run python -m http.server -d docs 8000   # then open http://localhost:8000
```

---

## Customize: a different voice

This is the most common tweak, and it's a two-line edit. The installed Kokoro model ships dozens of
voices (US/British/etc., several languages).

1. **Hear the options** on a book's own text, then pick by ear:
   ```sh
   uv run audiobook audition data/sources/rerum-novarum.html --voices bm_george,bm_lewis,am_michael,af_heart
   # listen to build/audition/*.mp3
   ```
2. **Add your pick** to `pipeline/voices.yaml` (give it a player id + label):
   ```yaml
   voices:
     lewis:
       ref: bm_lewis
       label: "Lewis — British narrator"
   ```
3. **Point the book's recipe at it** — edit `"voices"` in `data/books/rerum-novarum.json`
   (e.g. `["lewis"]`, or `["george","lewis"]` for two selectable narrators), then:
   ```sh
   uv run audiobook regenerate rerum-novarum --clean   # --clean wipes old audio so you don't mix voices
   ```

**Voice ids reference** (prefix = language: `a`=US, `b`=British, `e`=Spanish, `i`=Italian,
`p`=Portuguese, `f`=French; `f_`/`m_` = female/male). List what's installed:

```sh
uv run python -c "import numpy as np; from pipeline import config; \
  print(sorted(set(np.load(config.KOKORO_VOICES).files)))"
```

> If a voice fumbles a name or Latin phrase, add a pronunciation hint to the `lexicon` in
> `voices.yaml` (e.g. `"Rerum Novarum": "Rerum no-VAR-um"`) and re-audition. Tuning by ear is
> expected, not a failure.

---

## Other easy customizations

- **Faster/slower default narration:** `WPM`/pacing live in `pipeline/config.py`; the player also
  has a live speed control, so you rarely need to touch this.
- **Re-chapter a book:** edit its `data/chapter_maps/<id>.json` (verbatim opening-phrase anchors),
  then `regenerate`. See the [authoring guide](authoring-a-new-book.md) for how chapter maps work.
- **Don't host the audio at all:** just keep your rendered MP3s local. The site reads them from
  `docs/audio/`; nothing forces them online.

## What you can and can't redistribute

Rendering for **yourself** is fine. **Publishing** your rendered audio is governed by the source
text's rights — see the [copyright & permissions playbook](../WORK-QUEUE.md#copyright-and-permissions-playbook).
Short version: public-domain texts (e.g. *Rerum Novarum*, 1891) are free to share; the Vatican's
modern texts are reproducible **free, non-commercial, with attribution, not sold separately**; for
anything in copyright, get permission or keep it to your own private listening. *Not legal advice.*
