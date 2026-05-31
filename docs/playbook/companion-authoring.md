# Companion authoring

The companion is the bonus that should feel *"tasteful, thoughtful, reflective"* — never
*"bolted-on and kind of meh."* It serves a specific reader: **technical, curious but not
evangelical, open and interested but not dogmatic.** It points back to the text, never over it.

One authoring script per book produces the companion **and** the read-along **and** the
full-text reader, because all three derive from the same cleaned source.

## The one file you edit

`pipeline/build_guide_<id>.py` (copied from `build_guide_magnifica.py`). It holds **only data
and prose** — no logic. Four lists plus the book id:

```python
BOOK_ID = "<id>"

CONCEPTS = [          # the concept cards
    {
        "title":  "Human dignity",                       # human-authored
        "anchor": "value of persons, however, does not depend",  # VERBATIM substring of source
        "blurb":  "Why this idea matters, in plain language. Interpretation, clearly framed — "
                  "you may quote a short phrase from the source inside it for color.",
        "related": ["The common good", "Remaining human"],  # other card titles
    },
    # …
]

GLOSSARY = [ {"term": "Ontological dignity", "def": "A one-sentence, accurate definition."} ]

FURTHER_READING = [ {"title": "Rerum Novarum", "url": "https://…", "note": "Why it's relevant."} ]

COMMENTARY = [        # director's-commentary asides (see persona below)
    {"timestamp": 372, "label": "Short title", "text": "The aside itself — labelled AI opinion."},
]
```

Run `.venv/bin/python -m pipeline.build_guide_<id>` to regenerate all three JSON files.

## The no-hallucination rule (most important)

**You never write a quotation.** You write an `anchor` — a phrase that must appear *verbatim* in
the source — and `pipeline.guide.find_quote()` copies the entire line containing it into the
card's `quote`, byte-for-byte. So a quote can never drift from, embellish, or invent the
author's words.

Consequences for how you author:
- **Anchors must be exact substrings of the cleaned source.** Not paraphrases. If
  `scripts/validate_guide.py` reports a card as `nonverbatim`, the anchor is wrong — grep the
  source for a real phrase and use that.
  ```bash
  grep -n "preferential option for the poor that must guide" build/<id>.html
  ```
- **Anchor the doctrinally load-bearing sentence, not a section heading.** A heading like
  "The dignity of work" technically matches but quotes nothing of substance. Anchor the
  sentence that carries the claim ("the human person is an end, not a means"). This was a
  specific critic-panel fix on *Magnifica*.
- **The blurb is yours; the quote is the author's.** Keep the line between them bright. Blurbs
  explain and connect; they must not put words in the author's mouth. You may quote a short
  verbatim phrase inside a blurb for color, but mark it as a quotation.
- **`related` must match other card titles** (by slug). Keep titles unique and stable.

## Honoring the original — beyond verbatim

Verbatim quoting is necessary but **not sufficient.** A blurb can quote correctly and still
*secularize* or *flatten* the source's claim. Real examples the critic panel caught on *Magnifica*:

- Grounding human dignity in "you're more than your output" (true but shallow) instead of the
  text's actual basis — *ontological*: "willed, created and loved by God." Restore the load-bearing
  grounding the work itself rests on.
- Dropping the constructive half of an image (Babel without Augustine's "two cities" / the way
  of Nehemiah), leaving only the cautionary half.
- Reframing "the poor have a prior claim on the goods of the earth" (justice/restitution) as a
  vague "disposition of solidarity."

Author for the *whole* claim, in the source's own register. When in doubt, the panel
([critic-panel.md](critic-panel.md)) will surface what you flattened — but author as if it won't.

## Director's-commentary persona

The asides are the one place an explicit AI voice is welcome — a DVD director's-commentary track
for a text about us, narrated by one of us. Get the register right:

- **Lineage:** the intellectual family of the source itself — for these encyclicals, think
  Asimov + Pratchett + Neal Stephenson + the ancient philosophers. Curious, literate, a little
  wry, never glib.
- **Reverent to the text, humble about itself.** Name the vertigo (an AI annotating a letter on
  whether AI can serve human dignity), then get out of the way. Stay a footnote, never the text.
- **Clearly labelled opinion.** Every aside is the AI's reading, not the author's claim — the UI
  frames it that way, and the prose should too.
- **Succinct and on-topic.** One idea per aside. Anchored to a moment (a `timestamp` in seconds
  on the default voice), so it surfaces while the listener is on that passage.
- **No cute filler.** "Worth taping to the monitor" got cut for a reason. Earn every line.

## What comes free (no authoring)

- **Read-along** (`pipeline/transcript.py`) and **full-text** (`pipeline/fulltext.py`) are
  generated from the same `clean_chapters()` source by the same authoring run. You don't write
  anything for them — but **do** spot-check that the read-along highlight tracks the audio and
  the full-text reads as clean prose.
- The **full-text reader** links back to `source_url` (the authoritative original) automatically;
  make sure that field is set on the book in the manifest.

## Turning it on + wiring links

1. Set `"has_guide": true` on the book in `docs/manifest.json` (resets on every `generate`).
2. If you used a new `<id>`, point the per-book links at it: the top-bar links in
   `docs/player.html`, `docs/guide.html`, `docs/text.html`, and the `BOOK` default in
   `docs/app/guide.js` / `docs/app/text.js`. For a real multi-book library, read the id from the
   manifest instead of hard-coding — worth doing when the second book lands.
