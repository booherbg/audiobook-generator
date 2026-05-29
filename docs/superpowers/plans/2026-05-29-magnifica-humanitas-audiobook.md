# Magnifica Humanitas Audiobook — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans (inline, chosen for this goal-mode run) to implement task-by-task. Steps use checkbox (`- [ ]`) syntax.

**Goal:** Generate the *Magnifica Humanitas* audiobook (2 voices) from a deterministic local pipeline, play it in a vanilla-JS static player, and deploy live to GitHub Pages — then extend to a generic generator (Tier 2) and an audited interactive companion (Tier 3).

**Architecture:** A deterministic Python CLI (`audiobook`) turns a URL into chaptered, loudness-normalized MP3s + a `manifest.json`; a static vanilla-JS site reads the manifest and plays. No LLM in the pipeline — source-finding and Tier-3 authoring are Claude Code's job in-session. Build a thin **vertical slice** (1 chapter, both voices, deployed) before the full ~5-hour render.

**Tech Stack:** Python 3.12 (via `uv`), `kokoro-onnx` TTS, `ffmpeg`, `trafilatura`, `faster-whisper` + `jiwer` (QA), vanilla HTML/CSS/JS + `node:test`, `gh` for Pages.

**Reference spec:** `docs/superpowers/specs/2026-05-29-magnifica-humanitas-audiobook-design.md`

---

## File Structure

```
pyproject.toml                  # package "audiobook", deps, console_script; uv-managed .venv
Makefile                        # setup, test, slice, full, deploy shortcuts
pipeline/
  __init__.py
  __main__.py     # CLI: generate | audition | deploy | list  (argparse)
  config.py       # paths, constants (sample rate, bitrate, LUFS, wpm, model cache dir)
  resolve.py      # is_url/is_file → pass through; bare description → helpful error
  load.py         # HTMLLoader → Document{title, author, sections:[Section{heading, paragraphs}]}
  clean.py        # strip footnote markers, paragraph numbers, boilerplate
  normalize.py    # speakable text: numerals, abbreviations, quotes/dashes, lexicon
  chunk.py        # Document → [Chapter{index,title,segments:[str]}] (+ spoken intros, sub-split)
  tts.py          # KokoroTTS.synth(text, voice) → (samples: np.float32, sr); render_chunk → wav
  assemble.py     # ffmpeg: concat wavs + pauses, two-pass loudnorm, mono 64k mp3, id3 tags
  qa.py           # whisper WER vs source + ffmpeg signal checks → QAReport
  manifest.py     # load/insert/save docs/manifest.json (Book/Chapter/Voice models)
  voices.yaml     # voice ids → kokoro refs; pronunciation lexicon
  setup_models.py # download kokoro onnx + voices bin into cache
  tests/
    fixtures/      # tiny html snippet, expected text, ffmpeg-output samples
    test_resolve.py test_clean.py test_normalize.py test_chunk.py
    test_manifest.py test_qa.py test_load.py test_tts_smoke.py test_assemble_smoke.py
docs/
  index.html      # library grid
  player.html     # player
  about.html      # colophon (human + Claude)
  style.css
  app/
    logic.js      # pure: formatTime, resumeState, offsetOnVoiceSwitch, buildViewModel, nextPrev
    player.js     # DOM wiring + Media Session + localStorage + keyboard
  manifest.json   # generated
  audio/magnifica-humanitas/{female,male}/chapter-NN.mp3   # generated
  audio/magnifica-humanitas/cover.svg
  tests/
    test_logic.mjs # node:test over app/logic.js
  CHECKLIST.md    # manual cross-browser / mobile QA matrix
build/            # gitignored: raw html, cleaned text, wav, qa-report.json, models
.gitignore
```

---

## Phase 0 — Project skeleton & environment

### Task 0.1: Repo skeleton + .gitignore
- [ ] Create `.gitignore` (`build/`, `.venv/`, `__pycache__/`, `*.pyc`, `.DS_Store`, `node_modules/`).
- [ ] Create `pipeline/__init__.py`, `pipeline/tests/__init__.py`, `pipeline/tests/fixtures/`.
- [ ] Commit: `chore: project skeleton + gitignore`.

### Task 0.2: pyproject + uv venv (Python 3.12)
- [ ] Write `pyproject.toml`:

```toml
[project]
name = "audiobook"
version = "0.1.0"
requires-python = ">=3.12,<3.13"
dependencies = [
  "httpx>=0.27", "trafilatura>=1.12", "beautifulsoup4>=4.12", "lxml>=5",
  "kokoro-onnx>=0.4", "soundfile>=0.12", "numpy>=1.26",
  "faster-whisper>=1.0", "jiwer>=3.0", "pyyaml>=6", "pytest>=8",
]
[project.scripts]
audiobook = "pipeline.__main__:main"
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
[tool.hatch.build.targets.wheel]
packages = ["pipeline"]
```

- [ ] `uv venv --python 3.12 .venv` then `uv pip install -e .` (or `uv sync`).
- [ ] `brew install espeak-ng` (Kokoro phonemizer).
- [ ] Verify: `uv run python -c "import kokoro_onnx, soundfile, faster_whisper, trafilatura; print('ok')"`.
- [ ] Commit: `chore: pyproject + uv env (python 3.12)`.

### Task 0.3: Kokoro model fetch
- [ ] `pipeline/config.py`: `MODEL_DIR = Path("build/models")`, `SAMPLE_RATE=24000`, `MP3_BITRATE="64k"`, `LUFS=-16`, `WPM=155`, `OUT_SR=44100`.
- [ ] `pipeline/setup_models.py`: download `kokoro-v1.0.onnx` + `voices-v1.0.bin` from the kokoro-onnx GitHub release into `MODEL_DIR` (skip if present). (Look up the current release asset URLs at execution time; verify file sizes.)
- [ ] Run `uv run python -m pipeline.setup_models`; confirm files exist.
- [ ] Commit: `feat: kokoro model fetch`.

---

## Phase 1 — Deterministic core (TDD, pure functions)

Pattern for every task: write failing test → `uv run pytest <test> -v` (FAIL) → minimal impl → pytest (PASS) → commit.

### Task 1.1: `resolve.py`
- [ ] Test `test_resolve.py`: `resolve("https://x/y")=="https://x/y"`; `resolve("/tmp/f.html")` returns path if exists; `resolve("the pope's AI encyclical")` raises `ResolveError` with message containing "Ask Claude Code".
- [ ] Impl: `urllib.parse.urlparse` scheme in (http,https) → URL; `Path.exists()` → file; else raise.
- [ ] Commit.

### Task 1.2: `clean.py`
- [ ] Test: input paragraphs with footnote markers (`"dignity.[12]"`, `"work.¹"`) and leading paragraph numbers (`"23. The human person…"`) → cleaned (`"dignity."`, `"work."`, `"The human person…"`); boilerplate lines (e.g., `"Copyright © Dicastero"`) dropped.
- [ ] Impl: regex strip `\[\d+\]`, superscript digits (`¹²³⁰-⁹`), leading `^\d+\.\s+` on paragraph starts; drop lines matching a small boilerplate set.
- [ ] Commit.

### Task 1.3: `normalize.py`
- [ ] Test each rule: `"Leo XIV"→"Leo the Fourteenth"`; `"Chapter IV"→"Chapter Four"`; `"cf. Gn 1:27"→"see Genesis 1:27"` (or at least expand `cf.`→`see`); `"e.g."→"for example"`, `"i.e."→"that is"`, `"St."→"Saint"`; curly quotes/`—`/`…` normalized; lexicon term from `voices.yaml` (`"Rerum Novarum"`) maps to its phonetic hint if present.
- [ ] Impl: ordered regex passes + a roman-numeral helper limited to name/heading contexts; load lexicon via `pyyaml`.
- [ ] Commit.

### Task 1.4: `chunk.py`
- [ ] Test: a `Document` with 2 sections → 2 `Chapter`s; each gets a spoken intro segment (`"Chapter One. <title>."`); a section whose estimated minutes (words/WPM) exceeds `max_min` splits into ≥2 chapters at paragraph boundaries; sentences within a paragraph are segmented (split on `. ! ?` keeping abbreviations intact).
- [ ] Impl: estimate via word count; greedy paragraph packing under `max_min`; intro prepend; simple sentence splitter with abbreviation guard.
- [ ] Commit.

### Task 1.5: `manifest.py`
- [ ] Test: `insert_book(manifest, book)` adds/replaces by `id`; round-trips through JSON; schema has `version, books[].{id,title,subtitle,author,date,source_url,description,cover,public,has_guide,voices[],chapters[]}`; chapter has `files{voice:path}` + `duration{voice:sec}`.
- [ ] Impl: dataclasses → dict; load/save JSON (create if missing); replace-by-id.
- [ ] Commit.

### Task 1.6: `qa.py` (metric functions)
- [ ] Test: `wer(ref, hyp)` via jiwer on a known pair; `parse_loudnorm(json_str)` extracts integrated LUFS + true peak from ffmpeg's loudnorm print; `parse_silences(stderr)` returns list of (start,dur) from `silencedetect`; `within_duration_band(actual, words, wpm, tol=0.4)` bool.
- [ ] Impl: thin wrappers + regex/JSON parse on sample fixture strings.
- [ ] Commit.

---

## Phase 1.5 — Loader (fixture-tested)

### Task 1.7: `load.py` HTMLLoader
- [ ] Save `tests/fixtures/sample.html` (a small vatican-style snippet: title, `<h2>` headings, numbered `<p>`s, a footnote sup).
- [ ] Test: `HTMLLoader().load(fixture)` → `Document` with title, ≥1 section with heading + paragraphs (footnote markers still present here — cleaning happens in clean.py).
- [ ] Impl: `httpx.get` for URLs / read for files; parse with `trafilatura.extract` (favouring structure) or BeautifulSoup targeting the vatican body; map `<h1/h2>`→section headings, `<p>`→paragraphs. `PDFLoader` stub raises `NotImplementedError`.
- [ ] Commit.

---

## Phase 2 — TTS + assembly (smoke-tested, integration)

### Task 2.1: `tts.py`
- [ ] Smoke test `test_tts_smoke.py` (mark `@pytest.mark.slow`): `KokoroTTS().synth("Hello there, friend.", "af_heart")` returns float32 samples len>0 at 24kHz; writing via soundfile yields a readable wav. (Skips if model not downloaded.)
- [ ] Impl: wrap `kokoro_onnx.Kokoro(model, voices)`; `synth(text, ref)`; `render_segments(segments, ref, out_wavs)`.
- [ ] Commit.

### Task 2.2: `assemble.py`
- [ ] Smoke test `test_assemble_smoke.py`: given 2 short wavs, `assemble_chapter(wavs, out_mp3, title, album, artist)` → mp3 exists; `ffprobe` reports 1 channel, 44100 Hz, duration ≈ sum + pauses.
- [ ] Impl: build inter-segment silence (400ms) via ffmpeg `anullsrc`; concat demuxer; two-pass `loudnorm` (measure JSON → apply); encode `libmp3lame -b:a 64k -ac 1 -ar 44100`; `-metadata` id3 tags. Helper `probe(path)` returns {channels, sr, duration}.
- [ ] Commit.

---

## Phase 3 — Vertical slice (1 chapter, both voices) ⭐

### Task 3.1: CLI wiring + `generate --max-chapters 1`
- [ ] `pipeline/__main__.py` argparse: `generate <resource> [--voices female,male] [--id] [--title] [--author] [--max-chapter-min 18] [--max-chapters N] [--samples-only]`; `audition`, `deploy`, `list`.
- [ ] `generate` flow: resolve → load → clean → normalize → chunk → (limit to `--max-chapters`) → for each voice: tts → assemble → collect durations → manifest insert → save.
- [ ] Run: `uv run audiobook generate <vatican-url> --max-chapters 1` → `docs/audio/magnifica-humanitas/{female,male}/chapter-01.mp3` + `docs/manifest.json`.
- [ ] Manually listen to ~30s of each: clear & pleasant? Note any lexicon fixes.
- [ ] Commit (audio + manifest): `feat: vertical-slice audio for chapter 1 (both voices)`.

---

## Phase 4 — Player (vanilla JS) + node:test

### Task 4.1: `app/logic.js` pure functions (TDD via node:test)
- [ ] `docs/tests/test_logic.mjs`: `formatTime(754)==="12:34"`; `nextPrev` clamps at ends; `offsetOnVoiceSwitch(t, fromDur, toDur)` clamps to `[0,toDur]`; `buildViewModel(manifest,'magnifica-humanitas')` returns book + chapters with per-voice file/duration; `computeResumeState` reads/writes a plain object store.
- [ ] Run: `node --test docs/tests/` → FAIL, then implement `logic.js` (ES module exports), → PASS.
- [ ] Commit.

### Task 4.2: `player.html` + `player.js` + `style.css`
- [ ] DOM: title/author, cover, current-chapter, transport (⏮ ⏪15 ▶/⏸ 30⏩ ⏭), seek bar + times, speed `<select>` (0.75–2.0), voice toggle, chapter list (current highlight, completed ✓, durations), Library link, About link.
- [ ] Behaviors: load manifest (`?book=`), `<audio preload="metadata">`, resume + remember voice/speed (localStorage), voice switch preserves chapter+offset, keyboard (space, ←/→, `[`/`]`), **Media Session API** (metadata + action handlers), mobile-first responsive CSS, ARIA labels + focus styles.
- [ ] `index.html` library grid from manifest; `about.html` colophon; `cover.svg` simple titled card.
- [ ] Manual: open `python -m http.server` in `docs/`, verify slice plays, seeks, speeds, switches voice, resumes.
- [ ] Commit: `feat: vanilla-JS audiobook player`.

---

## Phase 5 — Deploy the slice (live)

### Task 5.1: `audiobook deploy` + enable Pages
- [ ] Impl `deploy`: `git add docs/` → commit → push; ensure Pages via `gh api -X POST repos/{owner}/{repo}/pages -f source.branch=main -f 'source.path=/docs'` (if 409/exists, `PUT` to update); print `https://booherbg.github.io/audiobook-generator/`.
- [ ] Run `uv run audiobook deploy`; wait for build; **load the live URL on desktop + phone**; confirm the slice plays end-to-end (range-request seeking works).
- [ ] Commit: `feat: deploy command + live Pages (vertical slice)`.

---

## Phase 6 — Full render + audio QA

### Task 6.1: Full generation
- [ ] `uv run audiobook generate <vatican-url>` (all chapters, both voices) — run as a **background task** (long). Sub-split keeps tracks ≤ ~18 min.
- [ ] Spot-check several chapters by ear (incl. Latin terms); update `voices.yaml` lexicon + re-render affected chapters if needed.

### Task 6.2: QA gate
- [ ] `qa.py` end-to-end: per track, run loudnorm-measure + silencedetect + duration-band, and faster-whisper on sampled 60s windows → WER vs normalized source. Write `build/qa-report.json`; print summary; non-zero exit on failures. Wire `deploy` to refuse if QA failed (unless `--force`).
- [ ] Run QA; fix outliers; commit full audio + manifest: `feat: full Magnifica Humanitas audiobook (both voices) + QA pass`.
- [ ] Redeploy; reconfirm live.

### Task 6.3: Tier-1 green
- [ ] `uv run pytest -q` and `node --test docs/tests/` both pass. Fill `docs/CHECKLIST.md` results (Chrome/Firefox/Safari desktop + iOS Safari + Android Chrome: play/seek/speed/voice/resume/MediaSession/responsive/keyboard).
- [ ] Commit: `test: Tier-1 suites green + QA checklist`.

---

## Phase 7 — Tier 2: generic generator (stretch)

### Task 7.1: Generalize + `list`/`audition`
- [ ] Confirm `generate <url>` is content-agnostic (id/title/author from flags or `<title>`/loader; default `--id` slug from title). `audiobook list` prints library. `audiobook audition <url> --voices af_heart,af_bella,af_nicole,am_michael,am_adam,am_fenrir` renders ~30s samples to `build/audition/`.
- [ ] Add `test_cli_generate_slug` (mock load/tts/assemble) verifying slug + manifest insert.
- [ ] Document in `README.md`: "describe-it" path = ask Claude Code in-session for the URL, then `generate`.
- [ ] Commit: `feat: generic generator + audition + list (Tier 2)`.

---

## Phase 8 — Tier 3: interactive companion medium (bonus)

*Its detailed design is a dedicated **envisioning pass** first (per spec §14). Multi-agent audit loop runs as Claude Code subagents.*

### Task 8.1: Envisioning pass → mini-spec
- [ ] Produce `docs/superpowers/specs/2026-05-29-companion-medium-design.md`: concept inventory, interaction model (ambient/opt-in), data schema `docs/guide/<book>.json`, external-reference policy (regenerate-from-cited-data + link-out + verify), commentary persona + modalities (footnotes / ducked voiced track / enriched woven edition), resolve the borrowed-media tension.

### Task 8.2: Grounded guide generation + audit
- [ ] Generate `guide/<book>.json` grounded in `build/<book>.clean.txt` (every claim quotes a passage + chapter/timestamp anchor); external refs fetched & verified; commentary clearly labeled.
- [ ] Adversarial audit loop (subagents, distinct lenses: fidelity-to-source, external accuracy, neutrality/respect, clarity, engagement, anti-drivel) → revise until all pass. *(If multi-agent Workflow is warranted, surface a token estimate first.)*
- [ ] `guide.html` + `app/guide.js`: ambient concept affordances, expand cards, "▶ listen" jump into player, glossary, further reading; set `has_guide:true`; player shows "Companion" link.

### Task 8.3: Director's-commentary + enriched edition (deepest stretch)
- [ ] Commentary content (persona: Asimov/Pratchett/Stephenson/ancients; reverent-to-text), timestamp-anchored; optional **enriched edition** = woven audio (chime + commentary voice at respectful breaks) as a separate MP3 set + `editions` field in manifest; player edition toggle.
- [ ] Audit + verify; deploy.

---

## Phase 9 — Final audit (world-class)

### Task 9.1: Quality sweep
- [ ] All tests green (`pytest`, `node:test`). Full manual matrix re-run. QA report clean.
- [ ] Adversarial quality audit of the whole published site + manifest (accessibility, mobile, accuracy, respect, polish) via subagents; fix findings.
- [ ] `README.md` finalized; colophon accurate. Final deploy; confirm live end-to-end.
- [ ] Commit: `chore: final quality audit + publish`.

---

## Self-Review notes (spec coverage)

- Spec §7–§12 (pipeline, TTS, encoding, manifest) → Phases 0–3, 6. §10 QA → Phase 6.2 / `qa.py`. §13 player (controls, resume, Media Session, a11y, browser matrix) → Phase 4 + 6.3. §15 deploy → Phase 5. §16 tests → Phases 1/4/6.3. §6 "no LLM in pipeline" → `resolve.py` (Task 1.1). §2 Tier 2 → Phase 7. §14 Tier 3 (companion, commentary, enriched edition, audit loop) → Phase 8. §1 colophon → Task 4.2. Acceptance §19 Tier-1 items 1–7 → Phases 3/4/5/6.
- Pragmatism: vertical slice (Phase 3+5) reaches a live, playable result before the multi-hour full render (Phase 6).
