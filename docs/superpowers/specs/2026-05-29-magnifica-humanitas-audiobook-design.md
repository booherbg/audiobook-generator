# Magnifica Humanitas Audiobook + Reusable Generator — Design Spec

**Date:** 2026-05-29
**Status:** In review (pre-plan)
**Author:** Blaine Booher (with Claude)

## 1. Overview & Goals

Build a **local audiobook generator** and a **static web player**, then publish to GitHub Pages.

1. **First asset:** Pope Leo XIV's encyclical *Magnifica Humanitas* as a chaptered, friendly-voiced
   audiobook (two voices).
2. **Reusable tool:** A CLI that takes a URL or local file directly, or a free-text description that
   **Claude Code (this session) finds for you** via in-session web search — and produces a new
   audiobook plus a manifest entry. No API keys, no hosted models: the only "LLM" in the loop is
   Claude Code itself.
3. **Static, browser-based player** on GitHub Pages: play, pause, seek, change speed, switch voice,
   navigate chapters, resume position. Works well on mobile.
4. **Quality is an objective:** UX, cross-browser, mobile/touch, **audio quality ("pleasant &
   clear")**, and test coverage are explicit acceptance criteria.
5. **Bonus (stretch):** an audited, hallucination-free, **interactive companion medium** —
   in-context exploration of the resource's foundational topics, verified external references
   (Wikipedia, data-driven charts), and discovery of related resources to read/listen to. Optional
   and never distracting.

The architecture splits into a **generation pipeline** and a **player**, joined by one interface:
**`manifest.json`**. The pipeline produces audio + a correct manifest; the player reads a manifest
and plays. Adding a book later is "run the pipeline, commit."

**Spirit & authorship.** This is a human + AI collaboration — Blaine (engineer/tinkerer) and Claude
(creative partner) — and that isn't incidental: the encyclical itself argues AI should serve human
dignity rather than concentrate power, so building a free, accessible, honest edition of that text
*together* is a small, literal instance of the partnership it calls for. The site carries a short,
honest colophon saying so — plainly, not as marketing. Throughout, the bar is genuine craft over
"AI-generated drivel."

## 2. Scope & Phasing (tiers)

Autonomous ("goal mode") runs should treat **Tier 1 as the definition of done**, Tier 2 as stretch,
Tier 3 as explicitly optional.

- **Tier 1 — Core audiobook (must-have).** fetch → clean → normalize → chunk → Kokoro (×2 voices) →
  ffmpeg → manifest for *Magnifica Humanitas*; **audio QA** (signal + intelligibility); the player
  (all controls, resume, mobile, Media Session, a11y, browser compat); `pytest` + `node:test`;
  deploy to Pages. **No LLM on this path.**
- **Tier 2 — Reusable generator (near-term).** `audiobook generate <url|file>`. The "describe it and
  find it" step is done by **Claude Code in-session** (the WebSearch/WebFetch I already used to
  locate this encyclical), not by pipeline code. (PDF loader deferred; headless `claude -p` / MCP is
  a possible future hook, not built now.)
- **Tier 3 — Interactive companion medium (bonus / final stretch).** The audited, grounded,
  exploratory medium in §14 — designed *world-class* in a dedicated envisioning pass once Tiers 1–2
  are buttoned up, then built incrementally. Includes an optional AI "director's commentary" mode.
  Its own plan; opt-in multi-agent workflow for both the design and the audit loop.

## 3. Non-Goals (this iteration)

- **PDF ingestion** — loader interface accommodates it; not implemented now (HTML source is clean).
- **Password protection / private books** — *Magnifica Humanitas* is public; true auth is impossible
  on plain Pages. For future private books: separate private repo or Cloudflare Access (not
  client-side "obfuscation"). Deferred.
- **Self-hosted local models** (Ollama/LM Studio/llama.cpp) — a *future* option once the hardware's
  ready; not today. The LLM today is Claude Code.
- **Offline/service-worker caching** — later.

## 4. Source Document

- **Title:** *Magnifica Humanitas — On Safeguarding the Human Person in the Time of Artificial
  Intelligence.* **Author:** Pope Leo XIV. **Signed** 15 May 2026, **released** 25 May 2026.
- **Length:** ~42,300 words, **5 chapters** → ~4.5–5 hours of audio.
- **Primary source (clean, paragraph-numbered HTML):**
  `https://www.vatican.va/content/leo-xiv/en/encyclicals/documents/20260515-magnifica-humanitas.html`
- **Backup mirror:** National Catholic Register CNA full-text page.
- We keep a **local cleaned-text copy** as the grounding source of truth (used by QA and the Tier-3
  study guide).

## 5. Architecture

```
                  ┌──────────────────── generation pipeline (Python CLI) ─────────────────────┐
 url | file ──────┼▶ load → clean → normalize → chunk → TTS(×2) → assemble → QA                │
                  │  (HTML)  (strip) (speakable)(chapters)(Kokoro)(ffmpeg:    (whisper +        │
                  │                                                pauses,     ffmpeg checks)   │
                  │                                                loudnorm,mp3)                │
                  └───────────────────────────────────────────────────────┬───────────────────┘
   "describe it"  ─── handled by Claude Code in-session (web search) ──▶ url
                                                       docs/manifest.json   ▼  + docs/audio/<book>/<voice>/*.mp3
                  ┌──────────────────── static site (vanilla JS) ──────────┴───────────────────┐
                  │ index.html (library)  player.html?book=<id>   ⋯ guide.html?book=<id> (Tier3)│
                  └───────────────────────────────────────────────────────┬───────────────────┘
                                                     audiobook deploy       ▼  git push + gh Pages
                                                   https://booherbg.github.io/audiobook-generator/
```

## 6. Repository Layout

```
pipeline/
  __main__.py     # `audiobook` CLI (generate | audition | deploy | list)
  resolve.py      # validate/normalize a URL or file path (the "find it from a description"
                  #   step is Claude Code's job, in-session — not pipeline code)
  load.py         # HTMLLoader (now); PDFLoader interface (later)
  clean.py        # strip footnotes, paragraph numbers, boilerplate
  normalize.py    # speakable text: numerals, abbreviations, quotes/dashes, lexicon
  chunk.py        # chapters from headings + sub-split long chapters + spoken intros
  tts.py          # Kokoro (kokoro-onnx) → per-chunk WAV
  assemble.py     # ffmpeg: concat + pauses + loudnorm + mono 64k MP3 + ID3 tags
  qa.py           # audio quality: whisper intelligibility (WER) + ffmpeg signal checks
  manifest.py     # build/update docs/manifest.json
  guide.py        # (Tier 3) packages study-guide JSON that Claude Code (subagents) generated + audited
  voices.yaml     # voice id → Kokoro voice; pronunciation lexicon
  pyproject.toml  # deps; console_script `audiobook`; pinned via uv (Python 3.12)
  tests/          # pytest: clean, normalize, chunk, manifest, resolve (url/path), qa, tts smoke

docs/             # ← GitHub Pages source (served from /docs on main)
  index.html      # library grid
  player.html     # the audiobook player
  guide.html      # (Tier 3) interactive study guide
  about.html      # short, honest colophon (how & why this was made)
  app/
    player.js     # DOM wiring
    logic.js      # pure logic: formatTime, resumeState, voiceSwitchOffset, buildViewModel
    guide.js      # (Tier 3) study-guide UI
  style.css
  manifest.json
  guide/<book>.json          # (Tier 3) generated, audited study-guide data
  audio/magnifica-humanitas/{female,male}/chapter-NN.mp3
  audio/magnifica-humanitas/cover.jpg
  tests/          # node:test over app/logic.js
  CHECKLIST.md    # manual cross-browser / mobile QA matrix

build/            # gitignored scratch: raw html, cleaned text, intermediate wav, qa-report.json
```

## 7. The Generator CLI

Run via `uv run audiobook <command>` (console entry point `audiobook`).

```
audiobook generate <url|file> [--id ID] [--title T] [--author A]
                              [--voices female,male] [--max-chapter-min 20]
                              [--samples-only] [--dry-run]
audiobook audition <url|file> [--voices ...]   # render ~30s samples per candidate voice only
audiobook deploy                               # commit docs/, push, ensure Pages on, print URL
audiobook list                                 # print library from manifest.json
```

**The only "LLM" is Claude Code (this session).** No API keys, no self-hosted models today (local
models are a *future* option once the hardware's ready). Intelligent steps run via local tooling —
me working in-session, Claude Code subagents, or optionally a headless `claude -p` / MCP call.

**Resource resolution (`resolve.py`):** a URL or existing file path is used directly — there is **no
LLM in the pipeline**. The "just describe it and find the source" capability is **Claude Code's job
in-session**: you ask me, I web-search (the same way I located this encyclical) and hand back the
canonical URL, then `audiobook generate <url>` runs the deterministic build. A bare description passed
straight to the CLI exits with: *"Ask Claude Code to find the source, then pass the URL."* (Future,
optional: a headless `claude -p` / MCP hook to script this with no human in the loop — not built now.)
**The Pope essay uses a direct URL → zero LLM on the critical path.**

**Loader interface** — `Loader.load(url_or_path) -> Document{title, author?, sections:[{heading,
paragraphs:[str]}]}`: `HTMLLoader` now (`httpx` + `trafilatura`, vatican.va body extraction);
`PDFLoader` later (defined, raises `NotImplementedError`).

## 8. Generation Pipeline (best practices baked in)

1. **Fetch**; keep a raw copy under `build/`.
2. **Clean (`clean.py`):** extract body; drop boilerplate; **strip footnote markers + paragraph
   numbers**; keep headings. Write the cleaned text to `build/` (grounding source of truth).
3. **Normalize (`normalize.py`)** for narration: "Leo XIV" → "Leo the Fourteenth"; Roman numerals in
   names/headings; expand cf./e.g./i.e./St./no.; numbers/dates to words where it aids speech; smart
   quotes/em-dashes/ellipses → speakable; collapse whitespace; **pronunciation lexicon**
   (`voices.yaml`) for Latin/proper nouns (e.g., *Rerum Novarum*), tuned after the audition.
4. **Chunk (`chunk.py`):** split into 5 chapters by heading; **sub-split** any chapter past
   `--max-chapter-min` (default 20) at paragraph boundaries; prepend a spoken intro per track; feed
   TTS sentence-sized pieces. Runtime estimated at ~155 wpm.
5. **TTS (`tts.py`):** Kokoro renders each chunk to WAV, once per voice.
6. **Assemble (`assemble.py`):** ffmpeg concat with ~400 ms paragraph pauses; **loudnorm to −16
   LUFS** (`I=-16:TP=-1.5:LRA=11`, two-pass); encode **mono 64 kbps MP3, 44.1 kHz**; ID3 tags.
7. **QA (`qa.py`):** see §10.
8. **Manifest (`manifest.py`):** insert/replace the book entry with per-voice file paths + measured
   durations.

## 9. TTS & Voices

- **Engine:** Kokoro via **`kokoro-onnx`** (ONNX Runtime; good on Apple-Silicon CPU). Needs the
  Kokoro v1.0 ONNX model + voices file (downloaded by a setup step) and `espeak-ng` for phoneme
  fallback.
- **Two voices** in the player: one friendly female, one friendly male.
- **Audition step:** ~30 s samples of ~6 candidates — female `af_heart`, `af_bella`, `af_nicole`;
  male `am_michael`, `am_adam`, `am_fenrir` — pick 1 + 1 **by ear**. Provisional defaults:
  **`af_heart`** + **`am_michael`** pending the listen.

## 10. Audio Quality Verification ("pleasant & clear")

`qa.py` scores every generated track, writes `build/qa-report.json`, summarizes to console; failures
block `deploy` unless explicitly overridden.

- **Clear — intelligibility (automated, local, keyless):** transcribe sampled segments (first 60 s +
  one random 60 s per chapter) with a local **faster-whisper** model; compute **word error rate**
  (via `jiwer`) against the normalized source text. High match ⇒ clear, correctly-pronounced
  narration; flags garbling, dropped/duplicated words, gross mispronunciation, truncation. Gate:
  WER ≤ ~10 % per sample (tunable), else flag for human review.
- **Clean — signal (automated, ffmpeg):** integrated loudness −16 ± 1 LUFS; true-peak ≤ −1 dBTP (no
  clipping); no unexpected silence gap > ~3 s mid-track (`silencedetect`); correct mono / 44.1 kHz;
  duration within the expected band (words ÷ wpm).
- **Pleasant — naturalness (layered):** (1) the by-ear **audition** voice pick; (2) a human
  **spot-check** of ≥ 2 full chapters per voice; (3) *optional* no-reference MOS prediction
  (NISQA / torchaudio-SQUIM) — best-effort, extra torch dep, **off by default**.

## 11. Audio Encoding & File-Size Policy

- Per-chapter **mono MP3, 64 kbps, 44.1 kHz**, −16 LUFS (~9 MB / 20-min track; ~150 MB/voice;
  ~300 MB for two).
- **Committed directly** under `docs/audio/…` — **not Git LFS** (Pages does not serve LFS files).
- **Auto-split safety valve:** chaptering keeps every track well under GitHub's **100 MB** per-file
  hard limit; oversized sources split further at paragraph boundaries.
- **Total-size fallback** (not expected at ~300 MB): host audio via GitHub Releases, player on Pages.

## 12. Manifest Schema (`docs/manifest.json`)

```json
{
  "version": 1,
  "books": [
    {
      "id": "magnifica-humanitas",
      "title": "Magnifica Humanitas",
      "subtitle": "On Safeguarding the Human Person in the Time of Artificial Intelligence",
      "author": "Pope Leo XIV",
      "date": "2026-05-15",
      "source_url": "https://www.vatican.va/content/leo-xiv/en/encyclicals/documents/20260515-magnifica-humanitas.html",
      "description": "Pope Leo XIV's first encyclical on AI and human dignity.",
      "cover": "audio/magnifica-humanitas/cover.jpg",
      "public": true,
      "has_guide": false,
      "voices": [
        { "id": "female", "label": "Heart (US, warm)",      "engine": "kokoro", "ref": "af_heart" },
        { "id": "male",   "label": "Michael (US, friendly)", "engine": "kokoro", "ref": "am_michael" }
      ],
      "chapters": [
        {
          "index": 1,
          "title": "Introduction",
          "files":    { "female": "audio/magnifica-humanitas/female/chapter-01.mp3",
                        "male":   "audio/magnifica-humanitas/male/chapter-01.mp3" },
          "duration": { "female": 372, "male": 365 }
        }
      ]
    }
  ]
}
```

Chapters are **text-aligned across voices**, which lets the player keep your place when switching voice.

## 13. The Player

Static site, manifest-driven.

- **`index.html`** — library grid of book cards (cover, title, author). One card now; future books
  appear automatically.
- **`player.html?book=<id>`** — the audiobook player.
- **`about.html`** — a short, honest colophon: how & why this was made (human + Claude, in the spirit
  of the text). Quiet, not marketing.

**Required features:** play/pause; prev/next chapter; skip back 15 s / forward 30 s; scrub seek with
current/total time; **speed** 0.75×–2.0×; **voice switch** (keeps chapter, clamps time offset);
**chapter list** (click to jump, current highlighted, completed checked, durations).
**Audiobook essentials:** **resume** last position; **remember voice + speed** per book (localStorage).

**UX / mobile / browser / a11y (acceptance criteria):**
- **Mobile-first responsive**, touch targets ≥ 44 px, one-handed use.
- **Media Session API** — lock-screen / media-key controls with chapter metadata + artwork.
- **Browser compat:** Chrome, Firefox, Safari desktop + iOS Safari + Android Chrome. MP3 universal;
  handle Safari user-gesture-to-play; `preload="metadata"`; rely on Pages HTTP **range requests** for
  seeking.
- **Accessibility:** semantic controls, ARIA labels, visible focus, keyboard shortcuts
  (space, ←/→, `[`/`]`).

```
┌───────────────────────────────────────────────┐
│  ◀ Library          Magnifica Humanitas         │
│  ┌───────┐          Pope Leo XIV                 │
│  │ cover │   Chapter 2 — The Dignity of Work     │
│  └───────┘   ◀◀  ⏪15   ▶/⏸   30⏩  ▶▶            │
│   ───────●──────────────────────  12:04 / 18:32  │
│   Voice: (●Female)( Male )   Speed: 1.0× ▼        │
│ ─────────────────────────────────────────────── │
│  Chapters                                         │
│   ✓ 1. Introduction                       6:12    │
│   ▶ 2. The Dignity of Work               18:32    │
│     3. Power & Concentration             14:50    │
└───────────────────────────────────────────────┘
```

**Code organization:** DOM wiring in `app/player.js`; **pure logic** in `app/logic.js` (`formatTime`,
`computeResumeState`, `offsetOnVoiceSwitch`, `buildViewModel`, next/prev) — ES modules, unit-tested
with `node:test` (no build step).

## 14. (Bonus · Tier 3) Interactive Companion Medium

*The final stretch goal — built only after Tiers 1–2 are green. Its design is itself a deliverable:
once we're buttoned up, a dedicated **envisioning pass** (a multi-agent workflow) imagines the
world-class version before we build it incrementally.*

**Vision.** A static, optional layer over the audiobook/text that lets a curious listener get real
context on the resource's **foundational topics** — *in place*, the moment "oh, interesting, I want
to dive into that" strikes — without ever derailing the listen. Ambient progressive disclosure: a
faint affordance on a concept; tap to expand a grounded explanation, a verbatim **quote**, a
**"▶ listen" jump** to that exact passage, related concepts, a glossary entry; tap away and it's gone.
Pristine "just listening" by default; deep and fascinating on demand.

**May include (designed properly later):**
- In-context **concept exploration** tied to where ideas appear in the text/audio.
- **Verified external references** (Wikipedia, primary sources) when they genuinely help.
- **Visuals** — charts/timelines preferably *regenerated by us from cited public data* (accurate,
  attributable, link-rot-proof) over hotlinked images; light **embedded HTML/JS** where interactivity
  earns its keep (concept map, timeline) — static, dependency-light, sandboxed.
- **Resource discovery** — related things to read/listen to, each verified, with the lovely loop of
  feeding a recommendation straight back into `audiobook generate` to grow the library.
- **"Director's commentary" mode** — an optional, toggleable track of **timestamp-anchored AI asides**
  (DVD cast-commentary vibe): text footnotes that surface at their moments, or a **voiced track** that
  ducks the narration. **Persona** — an "AI mirror" carrying the *same professionalism and
  intellectual lineage as the source*, drawing on the same references, philosophy, and eras the
  encyclical itself stands on (Catholic social teaching, natural-law philosophy, Leo XIII → Leo XIV);
  respectful, genuinely funny, and substantive on its own. Tonal influences: **Asimov** (lucid
  machine-ethics clarity), **Pratchett** (humane wit — and the footnote *is* his form), **Stephenson**
  (systems thinking + historical sweep; *Anathem*'s cloistered scholars rhyme with the text's own
  tradition), and **the ancient philosophers** (Socratic examination). Humor earned through erudition,
  never irreverence toward the subject; always hard-labeled and kept separate from the text and the
  verified facts.

**Non-negotiable bar:**
- **Optional & non-distracting** — off/collapsed by default; the core experience stays pristine.
- **Totally accurate** — the resource's own claims are RAG-grounded in the **local text** with quote
  citations and audio-timestamp verification (no hallucination); every *external* reference is
  **fetched and verified to exist and to say what we claim**, attributed with source + retrieval date,
  visually separated from the source's words. Any factual claim *inside the commentary* obeys the same
  no-hallucination rule. No fabricated citations, ever.
- **Respectful** — neutral, scholarly tone toward the text and its tradition; context, not editorial.
  The commentary may be personal and playful but is **never flippant toward the subject**, and is
  unmistakably marked as AI commentary, distinct from the source's words and from verified facts.
- **Authentic, not try-hard** — the persona is earned and genuine, never performative quirk; the bar
  is fascinating, never "AI-generated drivel."
- Held to the world-class-reference standard via the repeated **adversarial audit loop**
  (fidelity-to-source, external-reference accuracy, neutrality/respect, clarity, engagement,
  anti-drivel). Generation + audits run as **Claude Code subagents** (Max-plan session, not API or
  hosted models); revise until every lens passes. I'll propose the workflow (with a rough token
  estimate) for your OK rather than launching it unprompted.

**Open tension (resolve in the envisioning pass):** how far to go with borrowed web media — spectrum
from *link-out only* (safest) → *regenerate-our-own visuals from cited data* (accurate + respectful,
more work) → *embed/borrow graphics* (richest, but copyright + accuracy + link-rot risk). Default
lean: regenerate-from-cited-data and link-out; borrow only with attribution + a snapshot.

**Still static** — all enrichment generated offline into static JSON/HTML, served from Pages, **no
backend, no runtime LLM in the browser**. Sets `"has_guide": true`; the player reveals the companion
when present.

## 15. Deployment

`audiobook deploy`: `git add docs/`, commit, push; **idempotently ensure Pages serves `/docs` on
`main`** via the `gh` API (check, then create/update); print the live URL
`https://booherbg.github.io/audiobook-generator/`. Pages serves byte-range requests, so seeking works
with no backend.

## 16. Testing Strategy

**Python (`pytest`, TDD on the deterministic core):**
- `clean`: footnote/paragraph-number stripping; boilerplate removal.
- `normalize`: Roman numerals, abbreviation expansion, quote/dash handling, lexicon substitution.
- `chunk`: chapter split; sub-split threshold; spoken-intro insertion; sentence segmentation.
- `manifest`: schema; insert/replace; per-voice paths + durations.
- `resolve`: URL/path validation and the helpful error on a bare description. (Finding a source from
  a description is Claude Code's in-session job, not unit-tested pipeline code.)
- `qa`: metric functions on tiny fixtures — WER computation, loudness/peak/silence parsing,
  duration-band check.
- `tts`/`assemble`: **smoke test** on a one-sentence input — valid MP3, expected channels/rate; no
  hours-long renders in tests.

**JavaScript (`node:test`, zero build):** pure functions in `app/logic.js` — time formatting,
resume-state, voice-switch offset clamping, manifest→view-model, chapter next/prev.

**Manual matrix (`docs/CHECKLIST.md`):** Chrome / Firefox / Safari desktop + iOS Safari + Android
Chrome — playback, scrub-seek, speed, voice switch (position preserved), resume, Media Session
lock-screen controls, responsive layout, keyboard shortcuts.

**Tier 3 companion medium:** the adversarial audit loop is its test — fidelity-to-source, accuracy
of every external reference (each fetched & verified), neutrality/respect, clarity, engagement, and
anti-drivel must all pass; external links/visuals verified and attributed; commentary clearly marked
and free of false factual claims.

## 17. Tooling & Environment Setup

- **System Python 3.14 is too new for some ML wheels** → isolated **Python 3.12** env via **`uv`**;
  never touch system Python.
- `brew install espeak-ng` (Kokoro phonemizer); `ffmpeg` 7.1 present; `node` 22 present.
- Python deps: `httpx`, `trafilatura`, `kokoro-onnx`, `soundfile`, `numpy`, `faster-whisper`,
  `jiwer`, `pyyaml`, `pytest`. *(Optional MOS: `torch`/NISQA — off by default.)* No `anthropic`, no
  local-model or search SDKs — the pipeline is deterministic.
- **Tier 2/3 "LLM" = Claude Code (this session)** — nothing to host, no key, no extra dependency.
  (Self-hosted local models are a future option, not today.)
- Setup step downloads the Kokoro v1.0 ONNX model + voices file + the faster-whisper model.

## 18. Risks & Mitigations

| Risk | Mitigation |
|---|---|
| Python 3.14 lacks ML wheels | Pin Python 3.12 in an isolated `uv` venv |
| Kokoro mispronounces Latin/proper nouns | Audition + QA-WER surface them; fix via `voices.yaml` lexicon |
| Full render slow on CPU | Kokoro-ONNX is near/faster-than-real-time on Apple Silicon; run as a background task |
| Safari autoplay / seeking quirks | User-gesture to start; `preload="metadata"`; Pages range requests |
| Chapter boundaries unknown until fetch | Derived from real text; auto-split keeps tracks bounded |
| LFS unavailable on Pages | Commit MP3s directly; tracks stay < 100 MB |
| Tier 2/3 need an LLM | They run in **Claude Code** (this session / subagents) — nothing to host, no key; **Tier 1 needs no LLM at all** |
| Study-guide hallucination / fabricated refs | RAG grounding + quote citations + audio-timestamp verify; external refs fetch-verified |

## 19. Acceptance Criteria (tiered "definition of done")

**Tier 1 (must-have):**
1. `audiobook generate <vatican-url>` produces, for both voices, chaptered MP3s under
   `docs/audio/magnifica-humanitas/…` and a valid `docs/manifest.json`.
2. `audiobook audition` renders candidate samples; final two voices chosen by ear.
3. **Audio QA passes:** every track within signal thresholds; sampled STT-WER ≤ ~10 %; human
   spot-check confirms pleasant & clear.
4. Player supports play/pause/seek/speed/voice-switch/chapter-nav, resumes position, remembers
   voice + speed.
5. Player passes the manual matrix (Chrome/Firefox/Safari desktop + iOS Safari + Android Chrome),
   including Media Session controls and responsive mobile layout.
6. `pytest` and `node:test` suites pass.
7. `audiobook deploy` publishes to the live URL and it plays end to end.

**Tier 2 (stretch):**
8. Given a description, **Claude Code finds the correct source in-session** (already demonstrated by
   locating *Magnifica Humanitas*), then `audiobook generate <url>` builds it.

**Tier 3 (bonus):**
9. The interactive companion medium deploys; is optional/non-distracting; every claim about the text
   is grounded in a quoted passage with a working "▶ listen" jump; every external reference and visual
   is verified, attributed, and clearly separated from the source's words; the optional commentary
   mode is clearly labeled and factually clean; and it passes the adversarial audit loop on all lenses
   (incl. respect + external accuracy).

## 20. Future Extensions (noted, not built now)

- `PDFLoader`; LLM-assisted chaptering for unstructured texts.
- Self-hosted local models (Ollama/LM Studio/llama.cpp) once the hardware's ready.
- Private books: separate private repo or Cloudflare Access.
- Service-worker offline caching; download-for-offline.
- Per-book cover-art generation.
