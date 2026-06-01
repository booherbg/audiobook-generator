# Authoring a new book

Adding a text the repo doesn't have yet. This splits cleanly into **two parts** — and they have
very different character, so they're documented separately:

| | What it is | Who does it | Tooling |
|---|---|---|---|
| **Part 1 — Render** | Put the right assets in the right places, run the scripts. | Anyone. Deterministic. | The pipeline (`audiobook regenerate`) |
| **Part 2 — Prepare the assets** | Clean the text, chapter it, fix OCR/export defects, author the companion, run the critic panel. | **You + an LLM, working together.** Judgment-heavy. | An LLM operator (see below) |

The honest truth about the split: **Part 1 is easy and fast. Part 2 is where the real work is** —
and it's the part that, done by hand, is slow, fiddly, and error-prone. This pipeline was built in
the open assuming an LLM does Part 2 *with* you. That's not a shortcut or an embarrassment to hide
— it's the design.

---

## A note on what "LLM" means here (no API keys, no LLM in the code)

Important and easy to miss: **the pipeline itself contains no LLM and makes no API calls.** It's
pure deterministic Python — load → clean → chunk → TTS → assemble. The LLM is the **operator and
author** sitting *outside* the code: the one who reads the messy source, decides the chapter
breaks, spots the OCR typo a regex never would, writes the companion, and runs the critic panel.
It produces *tracked text artifacts* (a chapter map, a repairs map, a companion script) that the
deterministic pipeline then consumes.

So "LLM as a first-class part of the pipeline" means: **the inputs the pipeline needs are exactly
the things an LLM is good at producing**, and this guide is written to be handed *to* an LLM (or a
human + LLM) as the operating manual. This is what an AI-era authoring pipeline looks like — the
machine does the deterministic rendering; the intelligence (human or AI) does the preparation and
judgment, and leaves its work behind as reviewable files in git.

> **Why not do Part 2 by hand?** You can, but don't. Cleaning a Vatican HTML export means catching
> `R esponsibility` (a drop-cap artifact), `wages axe fair` (OCR), `ofrevolutionary` (a missing
> space), inline footnote markers narrated as "(9)", a stripped `<sup>th</sup>` turning "135th" into
> "one hundred thirty-five"… across thousands of paragraphs. Then chaptering a 14,000-word blob into
> a faithful structure, then authoring grounded concept cards with verbatim anchors, then a
> three-critic fidelity review. By hand: hours of tedium and missed corner cases. With an LLM: the
> LLM does the munging and proposes the judgment calls; you approve them. The pipeline's safety
> rails (verbatim-quote extraction, QA WER gate, critic panel) keep the LLM honest.

---

## Part 1 — Render (the easy half): assets → scripts → audiobook

The pipeline needs a small set of **tracked input files** per book, then one command does the rest.
The contract is the recipe at `data/books/<id>.json`, which names everything:

```jsonc
{
  "id": "laudato-si",                              // kebab-case; names every file + folder
  "title": "Laudato Si'", "subtitle": "On Care for Our Common Home",
  "author": "Pope Francis", "date": "2015",
  "source_url":  "https://www.vatican.va/.../laudato-si.html",   // attribution reference
  "source_file": "data/sources/laudato-si.html",   // the CANONICAL committed text snapshot
  "rights": "© Libreria Editrice Vaticana",        // shown to readers (attribution condition)
  "voices": ["female", "male"],                    // ids from pipeline/voices.yaml
  "chapter_map": "data/chapter_maps/laudato-si.json",  // or null if the source has usable headings
  "repairs": "data/repairs/laudato-si.json",       // or null if the source is clean
  "guide_builder": "pipeline.build_guide_laudato_si",  // the companion authoring module
  "wip": true                                      // shows a "work in progress" badge
}
```

The assets it references (all produced in Part 2):

| Asset | Path | Required? | What it is |
|---|---|---|---|
| **Source snapshot** | `data/sources/<id>.html` | **yes** | the frozen source text — guarantees offline, reproducible builds |
| **Recipe** | `data/books/<id>.json` | **yes** | the declarative build input above |
| **Chapter map** | `data/chapter_maps/<id>.json` | only if no usable headings | `[{title, anchor}]`, verbatim opening-phrase anchors |
| **Repairs map** | `data/repairs/<id>.json` | only if the export has defects | `{bad: good}` whole-word fixes |
| **Companion builder** | `pipeline/build_guide_<id>.py` | optional (for the companion) | concepts/glossary/commentary data |

Once those exist, **render is one command** (resumable; audio is a build artifact):

```sh
uv run audiobook regenerate <id>          # audio + read-along + full-text + companion
uv run audiobook regenerate <id> --skip-audio   # just the text layer (fast)
rm -f build/qa-report.json && uv run audiobook qa --id <id> \
   --source data/sources/<id>.html \
   --chapter-map data/chapter_maps/<id>.json --repairs data/repairs/<id>.json   # must print QA PASSED
uv run audiobook deploy
```

If you have all the assets, **that's the whole job.** The hard part is producing them — Part 2.

---

## Part 2 — Prepare the assets (the LLM-led half)

This is a workflow to run *with* an LLM (e.g. Claude Code in this repo). Each step produces a
tracked artifact. The deeper how-to for each lives in the existing references — this is the spine.

**Step 0 — Find & snapshot the source.** Have the LLM find the canonical full text (it searches;
the pipeline never does). Save the cleaned HTML to `data/sources/<id>.html` and commit it — this is
your reproducible source of truth, independent of the live URL.

**Step 1 — Inspect how it chunks.** Run it through the loader and look. Two checks (detailed in
[README.md §2.5](README.md)):
- *Usable chapters?* If it loads as one giant blob, you need a **chapter map** (Step 2).
- *Export defects?* Dump the cleaned paragraphs and skim for glued words, OCR substitutions, inline
  footnote markers, stranded drop-cap letters. These become a **repairs map** (Step 2).
This is pure LLM work — *reading the text for sense*, which no regex can do. (See the
[QA audit](qa-audit.md) for the catalog of defect types, and why heuristic word-splitting is
forbidden — it mangles real words.)

**Step 2 — Author the chapter map + repairs.** The LLM proposes thematic chapter boundaries
(channel a domain-appropriate "educator/historian" lens) with **verbatim** anchors, and a curated
`{bad: good}` repairs map for the specific defects it found. Both are small tracked JSON files. You
review and approve.

*Chapter-map rubric* (so this scales to long texts — Laudato Si' is ~38k words, ~2.5× RN):
- **Target ~8–14 min per chapter** (≈ 1,200–2,200 words at ~155 wpm). Aim for the number of
  chapters that gives that range; for a ~38k-word book that's roughly **15–25 chapters**. The
  chunker auto-splits anything over `MAX_CHAPTER_MIN` (18), so treat **~15 min as your soft ceiling**
  and don't hand-author a chapter longer than that.
- **Each `anchor` = a 4–8 word VERBATIM opening phrase** of the chapter, unique at that point in the
  text (grep to confirm it appears once, or first, where you mean). Not a paraphrase.
- **Follow the document's own argument**, not arbitrary length — break where the author pivots
  (problem → cause → response → …). Title each chapter for what it actually covers.
- **Validate before rendering** (no audio needed):
  ```python
  uv run python -c "import json; from pipeline.source_text import clean_chapters; \
    cm=json.load(open('data/chapter_maps/<id>.json')); rp=json.load(open('data/repairs/<id>.json')); \
    [print(f'{i:2} {sum(len(s.split()) for s in L[1:])/155:5.1f}min  {t}') \
     for i,t,L in clean_chapters('data/sources/<id>.html', chapter_map=cm, repairs=rp)]"
  ```
  Every anchor must resolve (a missing one raises `ValueError`), word counts should land in-band,
  and titles should read well. Iterate the map until they do.
- *Repairs:* only fix genuine export defects (glued words, OCR substitutions, stranded drop-caps) —
  **never** heuristically split words (it mangles real ones). Curate the `{bad: good}` list by hand
  from what Step 1 surfaced; it's short. The pipeline already strips inline `(N)` footnote markers
  and end-matter reference lists generically.

**Step 3 — Author the companion.** Clone the template and edit *data only*:
```sh
cp pipeline/build_guide_rerum.py pipeline/build_guide_<id>.py   # then edit BOOK_ID, CONCEPTS, etc.
```
The no-hallucination rule does the heavy lifting: you write an **anchor** (a phrase that must occur
in the source) and the code extracts the verbatim quote — the LLM can't invent quotations by
construction. Full guidance: [companion-authoring.md](companion-authoring.md) (concepts, the
director's-commentary persona, glossary, further-reading).

**Step 4 — Write the recipe** (`data/books/<id>.json`, shape above) and audition/pick a voice.

**Step 5 — Render + QA** (Part 1 commands). QA is the empirical gate: it Whisper-transcribes the
audio and checks WER against your text, so it catches any text/audio mismatch mechanically.

**Step 6 — The critic panel (the fidelity gate).** Dispatch domain-expert LLM reviewers to read the
companion *against the source* and iterate to a **HONORS** verdict. This is what keeps an LLM-
authored companion honest about the original. Full process + paste-ready prompts:
[critic-panel.md](critic-panel.md).

**Step 7 — `regenerate` + `qa` + `deploy`**, verify live.

---

## Why this is a good shape for an AI-era pipeline

- **The LLM's output is reviewable text in git**, not opaque model behavior baked into a binary. A
  chapter map, a repairs map, a companion script — anyone can read, diff, and correct them.
- **Determinism where it counts:** given the same tracked assets, the pipeline produces the same
  text every time. The LLM's judgment is captured *once* into files, then the build is mechanical.
- **Honesty rails the LLM can't route around:** verbatim quote extraction (no hallucinated quotes),
  the WER QA gate (audio must match text), the critic panel (fidelity to the source). The LLM does
  the fast, fallible munging; the deterministic checks catch its mistakes.
- **Reproducible without the LLM:** once the assets exist, a curious reader with no LLM can
  `regenerate` the book forever. The intelligence was needed to *author*, not to *run*.

That's the division of labor: **human sets intent and approves; LLM prepares and proposes;
deterministic pipeline renders and verifies.** Each does what it's best at.
