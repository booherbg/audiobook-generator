# Text-first builds — ship the text now, render the audio later

Audio is the slow, expensive half of a book: a full render runs for hours (so it usually runs
overnight), and every voice is its own MP3 set against the storage cap. The **text** experience —
read-along, full-text reader, the grounded companion, the critic-panel review — derives entirely
from the cleaned source and needs **no audio at all**. So the normal shape for a new edition is two
phases:

1. **Text-first, now** — build and ship the whole text layer to a critic-panel **HONORS** verdict,
   as a work-in-progress edition (in the Audiobook Queue). Hours of *your* judgment, zero render time.
2. **Audio, later (overnight)** — render the MP3s and close out the full Definition of Done.

This split is a **deferral, not a downgrade.** The risk it introduces is *drift*: a text-first build
quietly takes shortcuts the full audio-first path wouldn't, and if they aren't tracked they never get
fixed (a context compaction makes them invisible). This doc makes the loop airtight — every shortcut
is (a) made safe by a pipeline fallback *now*, and (b) written into a per-book checklist the audio
pass *must* close.

> **Worked example:** *Laudato Si'* was built this way. Its deferral checklist is in
> [BACKLOG.md](../../BACKLOG.md) → "Laudato Si' — audio render: the no-audio compromises to address."
> Copy it as the template for the next text-first book.

## Phase 1 — the text-first build

Do [authoring-a-new-book.md](authoring-a-new-book.md) Part 2 (find + snapshot source → chapter map →
repairs → companion), then render **only the text layer**:

```sh
uv run audiobook regenerate <id> --skip-audio    # companion + read-along + full-text, no MP3s
uv run python scripts/validate_guide.py <id> data/sources/<id>.html   # nonverbatim=NONE dead=NONE
```

Then run the [critic panel](critic-panel.md) to **HONORS** — the fidelity gate needs no audio (it
reads the companion against the source). Finally:

- `wip: true` in the recipe (`data/books/<id>.json`); audio voice can stay a placeholder.
- add the book to the **Audiobook Queue** (`docs/app/index.js` `QUEUE`) with `preview` links to its
  `guide.html?book=<id>` / `text.html?book=<id>` so it's reachable via the **5-tap admin** preview.
- `audiobook deploy`. The book stays **out of the public library** (no manifest entry yet) and lives
  in the Queue until it has audio.

## What gets deferred — and the fallback that keeps each safe

Anything that depends on **measured per-voice durations** or the **rendered MP3s** is deferred. Each
is made safe *now* by a fallback, and *closed* when audio lands:

| Deferred thing | Why (no audio) | Safe-now fallback | Close it at audio time |
|---|---|---|---|
| **Commentary placement** | asides map absolute seconds → `{chapter, fraction}` via real durations | `guide.py` synthesizes a **155-wpm reading timeline** when a book has no audio | a full `regenerate` rebuilds the guide against real durations; **re-verify each aside** lands on its passage |
| **Concept `timestamp` labels** | the label is computed on the voice timeline | label reads ~0/estimated; the deep-link **`fraction` is word-based and already correct** | refined automatically on rebuild |
| **Manifest entry + metadata** | `generate` writes the manifest from audio on disk | `guide`/`fulltext` fall back to the **recipe** for title/author/source_url/rights | render writes a real entry → **remove the book from the Queue** (it's a real WIP card now) |
| **Audio QA** (WER, loudness, clipping, silence, duration) | nothing to measure | *skipped* | **`audiobook qa --id <id>` → QA PASSED** — the gate that proves audio matches text |
| **Spot-listen + pronunciation** | nothing to hear | *skipped* | listen ch1 + a mid-chapter; add `voices.yaml` lexicon overrides for mangled names; re-render |
| **Library placement** | no player page without audio | Queue teaser + admin preview | normal WIP-badged library card once it has audio |

The first three are **automatic** (the pipeline handles them); the last three are **manual** and must
be on the checklist below.

## The deferral record — this is what stops the drift

When you ship a book text-first, **write its audio-render checklist into [BACKLOG.md](../../BACKLOG.md)**
(the concrete, per-book version of the manual items above) and drop a one-line memory pointer. This is
the mechanism that guarantees the loop closes — without it, the deferred items vanish at the next
compaction. The *Laudato Si'* checklist is the template; keep the same numbered shape.

## Phase 2 — the audio render (overnight): the QA loop that re-converges on audio-first

Work the book's checklist top to bottom:

1. **Audition + pick the voice(s)**; set them in the recipe (replace any placeholder).
2. **Render**: `uv run audiobook regenerate <id>` (no `--skip-audio`). Resumable; hours.
3. **Rebuild the companion** against real durations (the same `regenerate` does this).
4. **Re-verify commentary placement** — each aside still on its intended passage; nudge if drifted.
5. **Audio QA** — `audiobook qa --id <id>` must print **QA PASSED** (the Phase-1 skip, now closed).
6. **Pronunciation + spot-listen** — fix `voices.yaml`, re-render affected chapters, listen in the
   deployed player.
7. **Promote out of the Queue** — remove the book from `QUEUE` in `docs/app/index.js`; confirm
   `has_guide: true` on its manifest entry.
8. **Deploy + verify live** — endpoints 200; a byte-range request returns **206** (seeking).

## Definition of done, in two phases

- **Text-first done:** companion at **HONORS**, `validate_guide` clean, `pytest` + `node --test`
  green, deployed as a WIP/Queue edition, **deferral checklist written to BACKLOG + memory.**
- **Full done:** the above **plus** audio QA PASSED, spot-listened, real manifest entry, promoted out
  of the Queue — the full [Definition of Done](qa-audit.md#definition-of-done) with audio "in scope
  this round."

Until Phase 2, the edition is *honestly* a work in progress: complete and excellent in text, awaiting
its voice. That's a feature — it's how the library grows without waiting on render time.
