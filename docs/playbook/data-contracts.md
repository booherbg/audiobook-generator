# Data contracts

The player is static vanilla JS; it knows nothing about the pipeline except these four JSON
files. They are the interface. Keep them stable and the player and pipeline can evolve
independently.

All four live under `docs/` (the published site root). The pipeline writes them; the player
fetches them. Every text field ultimately derives from `pipeline/source_text.clean_chapters()`,
so on-screen words match spoken words.

| File | Written by | Read by | Purpose |
|------|-----------|---------|---------|
| `docs/manifest.json` | `pipeline/manifest.py` (via `generate`) | every page | library index, per-voice chapter files + durations |
| `docs/guide/<id>.json` | `pipeline/guide.py` | `docs/app/guide.js` | companion: concepts, commentary, glossary, further-reading |
| `docs/transcript/<id>.json` | `pipeline/transcript.py` | `docs/app/player.js` | read-along lines + timing fractions |
| `docs/text/<id>.json` | `pipeline/fulltext.py` | `docs/app/text.js` | full-text reader |

A core invariant ties three of them together: **voice-independent positioning.** Voices differ
in length by ~10%, so an absolute second on one voice's timeline lands in the wrong place — even
the wrong chapter — on the other. Therefore deep-links and read-along store
`{chapter, fraction}` (a chapter index + a position in `[0,1)` within it), and the player
resolves `fraction × duration[selectedVoice]` at click time.

---

## manifest.json

The library. One entry per book; chapters carry per-voice file paths and measured durations.

```jsonc
{
  "books": [
    {
      "id": "magnifica-humanitas",          // kebab-case; names audio dir + all JSON files
      "title": "Magnifica Humanitas",
      "subtitle": "On the Dignity of the Human Person…",
      "author": "Pope Leo XIV",
      "date": "2026",
      "source_url": "https://www.vatican.va/…",  // the authoritative original
      "description": "",
      "has_guide": true,                     // ← player shows Companion link only when true
      "cover": "audio/magnifica-humanitas/cover.svg",
      "public": true,
      "voices": [
        { "id": "female", "label": "Heart — warm US female",  "engine": "kokoro", "ref": "af_heart" },
        { "id": "male",   "label": "Michael — friendly US male", "engine": "kokoro", "ref": "am_michael" }
      ],
      "chapters": [
        {
          "index": 1,
          "title": "Humanity, Created in Grandeur",
          "files":    { "female": "audio/…/af_heart/chapter-01.mp3", "male": "audio/…/chapter-01.mp3" },
          "duration": { "female": 612.3, "male": 558.9 }   // seconds, per voice
        }
      ]
    }
  ]
}
```

**Rules / gotchas**
- `chapters[].files` and `chapters[].duration` are keyed by **voice id**. Both voices must be
  present for a chapter to be listed (`generate` only emits chapters complete across all voices
  on disk).
- `has_guide` defaults to **false**; set it `true` once after the companion exists —
  `generate`/`regenerate` then **preserve** it (no longer reset). (See playbook step 5.)
- `duration` is measured by `ffprobe`, not estimated — the read-along and deep-link math depend
  on it being real.

## guide/&lt;id&gt;.json

The companion. Written by `pipeline/guide.py` from the authoring data in
`pipeline/build_guide_<id>.py`. **Every `quote` is extracted verbatim from the source by code**
— the authoring script supplies an `anchor` (a phrase that must occur in the source) and the
builder copies the whole line containing it.

```jsonc
{
  "book": "magnifica-humanitas",
  "intro": "A companion to the reading — not a replacement for it. …",
  "concepts": [
    {
      "title": "Two loves, two cities",        // human-authored
      "blurb": "The other half of the central image…",   // human-authored, clearly interpretation
      "quote": "Two loves have built two cities…",        // VERBATIM, extracted from source
      "chapter": 9,
      "chapter_title": "…",
      "fraction": 0.41203,                      // voice-independent position within the chapter
      "timestamp": 4123.7,                      // display label only (default voice timeline)
      "related": ["Babel or the Beloved City"]  // titles of other cards (must resolve)
    }
  ],
  "glossary":        [ { "term": "Ontological dignity", "def": "…" } ],
  "further_reading": [ { "title": "Rerum Novarum", "url": "https://…", "note": "…" } ],
  "commentary": [                               // director's-commentary asides — labelled AI opinion
    {
      "label": "On 'never neutral'",
      "text":  "…",
      "chapter": 7, "chapter_title": "…",
      "fraction": 0.12, "timestamp": 4500.0
    }
  ]
}
```

**Rules / gotchas**
- `quote` is **never** hand-written. If you want a specific sentence quoted, set the card's
  `anchor` to a phrase inside it; the builder pulls the line. This is the no-hallucination
  guarantee — see [companion-authoring.md](companion-authoring.md).
- `related` entries are matched by slug to other cards' titles. A typo = a dead link; the
  integrity check (`scripts/validate_guide.py`) fails on it.
- Commentary is authored in **absolute seconds** (default-voice timeline) and converted to
  `{chapter, fraction}` by the builder, so it survives a voice switch like everything else.

## transcript/&lt;id&gt;.json

Read-along. One entry per chapter with the exact spoken lines and the cumulative fraction of the
chapter elapsed at each line's start.

```jsonc
{
  "book": "magnifica-humanitas",
  "chapters": [
    {
      "index": 1,
      "title": "…",
      "lines":  ["Humanity, Created in Grandeur.", "Humanity, created by God…", "…"],
      "starts": [0.0, 0.018, 0.041, …]         // fraction [0,1) at each line's start; ascending
    }
  ]
}
```

**Timing model (no forced alignment):** a line's spoken time ≈ its character count **plus** a
fixed inter-line gap, modelled as `PAUSE_CHARS` character-equivalents (`pipeline/transcript.py`).
The fixed gap keeps short lines (e.g. a one-line scripture reference) from being under-weighted —
the main source of drift in a naive char-proportional model. The player computes a line's start
as `starts[i] × duration[voice]` and binary-searches the current line from `currentTime`.

## text/&lt;id&gt;.json

Full-text reader. The whole work, chapter by chapter, for reading along or checking a passage.

```jsonc
{
  "book": "magnifica-humanitas",
  "title": "Magnifica Humanitas", "subtitle": "…", "author": "Pope Leo XIV",
  "source_url": "https://www.vatican.va/…",     // renders the "read the original at vatican.va" link
  "chapters": [
    { "index": 1, "title": "…", "paragraphs": ["…", "…"] }   // paragraphs = spoken lines minus the chapter-intro line
  ]
}
```

**Note:** `paragraphs` drops `lines[0]` (the spoken "Title." intro) so the page reads as prose,
not as a heading repeated under its own heading.
