# Playbook — adding another book

This folder is the **pull-and-go guide** for turning a new long-form text into a complete
edition: chaptered audiobook + web player + read-along transcript + full-text reader +
grounded companion, reviewed by a critic panel and gated by a world-class QA audit — the
exact process that produced *Magnifica Humanitas*.

Open this file, work top to bottom. The four references go deep where a step needs it:

| Doc | What it covers |
|-----|----------------|
| [data-contracts.md](data-contracts.md) | The JSON shapes the player reads: `manifest`, `guide`, `transcript`, `text`. The pipeline↔player interface. |
| [companion-authoring.md](companion-authoring.md) | Authoring the companion (`build_guide_<id>.py`), how read-along + full-text come free, the no-hallucination quote rule, commentary persona. |
| [critic-panel.md](critic-panel.md) | The "nerd review": three subagents (educator, humanist, domain-expert) read the companion *against the source* and iterate to a **HONORS** verdict. Ready-to-paste prompts + rubric. |
| [qa-audit.md](qa-audit.md) | The world-class QA audit: audio gates, site gates, companion integrity, live verification, and the artifact-the-user-sees rule. |

**Two principles run through everything:**

1. **Honor the original.** Every quote is extracted *verbatim* from the source by code, not
   typed by hand. Blurbs and commentary are clearly-labelled interpretation. The companion
   serves the text; it never speaks over it. The critic panel exists to enforce this — and
   verbatim quoting is *necessary but not sufficient* (a blurb can still secularize or flatten
   a claim, which is exactly what the panel catches).
2. **Verify the artifact the user sees.** "The JSON is correct" is not "the page works." Run
   the JS, hit the live URL, listen to the audio. We have shipped a blank companion page that
   passed every data check; the fix was a render test and a live curl. Don't repeat it.

---

## The pipeline in one breath

```
source (URL/file)
  └─ load → clean → chunk            pipeline/{load,clean,chunk}.py  → chapters of spoken lines
  └─ normalize → TTS → assemble      pipeline/{normalize,tts,assemble}.py (Kokoro ONNX + ffmpeg)
  └─ QA                              pipeline/qa.py (WER, loudness, silence, duration)
  └─ manifest.json                   pipeline/manifest.py (the player ↔ pipeline interface)
  └─ companion (optional)            pipeline/build_guide_<id>.py → guide + transcript + full-text
  └─ deploy                         pipeline/deploy.py (gh CLI → GitHub Pages)
```

The pipeline is **deterministic and contains no LLM** — finding the source from a description,
authoring the companion, and running the critic panel are the human + Claude-Code parts.
There are **no API keys and no console script**; everything is `.venv/bin/python -m pipeline …`.

The single source of truth for the *text* (audio, read-along, full-text, and companion quotes
all derive from it) is `pipeline/source_text.clean_chapters()` — load → clean → chunk, run once.
This is why the words on screen always match the words spoken.

---

## Storage cap (read before generating audio)

Per [BACKLOG.md](../../BACKLOG.md): the local disk is tight. **Do not generate new MP3s beyond
an agreed core set without explicit go-ahead.** A full book is ~34 MP3s (≈17 chapters × 2
voices). You can build and ship the *entire* text experience — read-along, full-text reader,
companion, critic review — with **zero new audio**, because those derive from the text, not the
MP3s. When audio is in scope, confirm the budget first.

---

## Runbook

### 0. One-time machine setup (skip if the venv already exists)

```bash
uv venv --python 3.12 && uv pip install -e .     # 3.12 — newer Pythons lack ML wheels
.venv/bin/python -m pipeline.setup_models        # fetches Kokoro ONNX (~350MB) to build/models/
```

### 1. Find and cache the source

Claude Code finds the canonical source in-session (web search), then cache the HTML locally so
every later step is fast and offline-reproducible:

```bash
# example for a Vatican encyclical — adjust the URL
curl -sL "<source-url>" -o build/<id>.html
```

Use a short, stable `<id>` (kebab-case), e.g. `rerum-novarum`, `laudato-si`. It names the audio
folder, the manifest entry, and every JSON file — keep it consistent everywhere.

> **Pronunciation:** Latin/foreign titles can trip the TTS. Add overrides to the `lexicon` in
> `pipeline/voices.yaml` (e.g. `"Rerum Novarum": "Rerum no-VAR-um"`) — applied before TTS to
> every voice. Preview with `audition` (next step) and tune until it reads well.

### 2. Audition voices, pick two

```bash
.venv/bin/python -m pipeline audition build/<id>.html --voices af_heart,am_michael
# listen to build/audition/*.mp3 — keep two with friendly, contrasting timbre
```

We ship two voices so listeners can choose: **`af_heart` ("Heart")** and **`am_michael`
("Michael")**. Stick with these unless a book calls for something different.

### 3. Generate the audiobook (resumable) — *audio budget required*

```bash
.venv/bin/python -m pipeline generate build/<id>.html \
    --id <id> --title "<Title>" --author "<Author>" --date "<year>" \
    --subtitle "<subtitle>" --source-url "<canonical-url>" \
    --voices af_heart,am_michael
```

- **Resumable.** A chapter already on disk (and plausibly complete: ≥0.6× expected duration)
  is skipped; a crash-truncated MP3 is re-rendered. Safe to re-run after any interruption.
- The manifest entry is rebuilt from **whatever audio is actually on disk**, scanning *all*
  configured voices — a single-voice re-render never drops the other voice.
- Long render (~hours for a full book). It auto-backgrounds; resume by re-running the same
  command. Render a slice first to smoke-test: `--chapters 1:1`.

### 4. Audio QA

```bash
rm -f build/qa-report.json                       # always start clean (report is resumable otherwise)
.venv/bin/python -m pipeline qa --id <id> --source build/<id>.html
```

Must print `QA PASSED`. Gates and how to debug failures: [qa-audit.md](qa-audit.md#audio).

### 5. Read-along + full-text + companion

All three are generated by one authoring script. **Copy the template and edit the data:**

```bash
cp pipeline/build_guide_magnifica.py pipeline/build_guide_<id>.py
# edit BOOK_ID and the CONCEPTS / GLOSSARY / FURTHER_READING / COMMENTARY data
.venv/bin/python -m pipeline.build_guide_<id>    # writes guide + transcript + full-text JSON
```

How to author well (anchors, blurbs, commentary persona, the no-hallucination rule):
[companion-authoring.md](companion-authoring.md). Read-along and full-text need **no authoring**
— they fall out of the shared source path automatically.

> **Gotcha — turn the companion on.** Set `"has_guide": true` on the book in
> `docs/manifest.json` so the player shows the Companion link. Re-running `generate` rebuilds the
> entry with `has_guide:false`, so flip it *after* your final generate (or just before deploy).

Wire the per-book links if you added a new id (the shipped pages hard-code
`?book=magnifica-humanitas`): the player/guide/text top-bar links and the `BOOK` default in
`docs/app/{guide,text}.js`. For a multi-book library, prefer reading the id from the manifest.

### 6. Companion integrity check

```bash
.venv/bin/python scripts/validate_guide.py <id> build/<id>.html
# concepts=N nonverbatim=NONE dead=NONE unique_titles=True   ← required
```

Any `nonverbatim` card means its `anchor` isn't an exact substring of the cleaned source — grep
the source for a real phrase and fix the anchor. See [qa-audit.md](qa-audit.md#companion-integrity).

### 7. Critic panel — the nerd review

Dispatch three subagents (educator, humanist, domain-expert appropriate to the book) to read the
companion *against the source*. Apply their findings, rebuild, re-run **until the verdict is
HONORS.** Full process + ready-to-paste prompts: [critic-panel.md](critic-panel.md).

This is not optional and not a rubber stamp. The *Magnifica* companion was **MOSTLY-HONORS**
until the panel caught secularized theology and a missing half of the central image; the fixes
are what made it world-class.

### 8. Tests

```bash
.venv/bin/python -m pytest -q                    # pipeline logic
node --test docs/tests/*.mjs                     # player logic + render guards
```

Both green. If you added a new page or render path, add a render guard test (the pattern that
catches blank-page regressions): [qa-audit.md](qa-audit.md#site).

### 9. Deploy + verify live

```bash
.venv/bin/python -m pipeline deploy              # commits docs/, pushes, ensures Pages
```

Then **verify the live site**, not just the local files — endpoints 200, concept count served,
render JS intact, audio seekable. Exact checks: [qa-audit.md](qa-audit.md#live-verification).

### 10. Definition of done

A book is done when **every** box in [qa-audit.md → Definition of done](qa-audit.md#definition-of-done)
is checked: audio QA passed, companion verbatim with no dead links, **critic verdict HONORS**,
all endpoints live, read-along + full-text working, link back to the original present, tests
green. Then cross-link it from the sibling editions and update `BACKLOG.md`.

---

## Next up (from BACKLOG.md)

The two documents *Magnifica Humanitas* is built on, each deserving this full treatment:

1. **Rerum Novarum** — Leo XIII, 1891 — the origin of Catholic Social Teaching.
2. **Laudato si'** — Francis, 2015 — integral ecology.

Together with *Magnifica* they form a small, connected library; the companions' further-reading
already points at them, so once they exist, make those live links between editions.
