# Companion authoring

The companion is the bonus that should feel *"tasteful, thoughtful, reflective"* — never
*"bolted-on and kind of meh."* It serves a specific reader: **technical, curious but not
evangelical, open and interested but not dogmatic.** It points back to the text, never over it.

One authoring script per book produces the companion **and** the read-along **and** the
full-text reader, because all three derive from the same cleaned source.

## The one file you edit

`pipeline/build_guide_<id>.py` (copied from `build_guide_rerum.py` — the template that already
wires a chapter map + repairs). It holds the `BOOK_ID`, the data lists (`CONCEPTS`, `GLOSSARY`,
`FURTHER_READING`, `COMMENTARY`), an optional `INTRO` string, and `CHAPTER_MAP`/`REPAIRS` path
constants that its small `main()` threads into build_guide/transcript/fulltext. So: mostly data
and prose, plus a thin `main()` — not "no logic, four lists":

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

Run `uv run audiobook regenerate <id> --skip-audio` to rebuild all three JSON files from the
recipe (it runs your `guide_builder`); `python -m pipeline.build_guide_<id>` is the low-level
equivalent.

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
  grep -n "preferential option for the poor that must guide" data/sources/<id>.html
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

## The voice in the margins — Andrew (persona charter)

The commentary asides are the one place an explicit, first-person voice speaks to the reader. That
voice is a **named character: Andrew** — introduced on the about page (`about.html#andrew`), which
is the canonical bio; the companion UI names him and links back to it.

**Canon first — read this before touching a word.** The commentary already shipped with *Magnifica
Humanitas* and *Rerum Novarum* — written *before* Andrew was named — **is the canonical voice,** and
it's the good thing we're protecting. Andrew is an **additive layer**: a name, a frame, and a
declared perspective placed *around* that reflection — **never** a license to rewrite, sand down, or
"improve" it. If the persona ever pulls against the genuine reflection, **the reflection wins.**
Naming the voice changes only *reception* — it lets a first-time reader meet that reflection *as a
character's* rather than dismiss it as faceless "AI commentary" before reading a line; it does not
touch the prose. Everything below is distilled *from* that canon to guide *new* asides — never a
standard to retrofit onto what already works.

**Why a character at all (it's the honesty, not a costume).** The project's spine is *a declared
thing is more honest than a hidden one* — the same logic as verbatim quotes. An unframed reflective
AI voice reads to a skeptic as unsubstantiated fluff and gets dismissed, and the floating "I" muddies
whether a person or a fiction is speaking. Naming the voice fixes both — it turns "wait, who?"
(confusion) into "ooh, who?" (intrigue) and gives the reflection a form a reader will actually meet.
We are **not** hiding that an AI is involved (the about page says so plainly); we are giving the
reflection a frame it can be received in.

**Two registers — keep them clean:**
- **Tooling layer** (narration, read-along, full-text, concept blurbs, glossary, quotes): exact,
  accurate, *voiceless*. No personality. The output of the work, not a character.
- **Fiction layer** (the asides): Andrew, who may wonder, flinch, and reflect — *because we've
  declared it's a character.* The rule that an undeclared AI must "describe, never perform feeling"
  relaxes here, **inside the fence**. That's the whole reason to name it.

**Out of world, total honesty / in world, permanent mystery.** The about page tells the truth about
how Andrew is *made* (a character Blaine wrote, voiced in the human+AI work). The asides are then
free to leave Andrew's *being* an open question — it knows it's something new, never announces what
it is, and we never resolve it. The reader is never deceived about the making; only the character's
self is left open. (Named for Asimov's Andrew, the servant robot who earns personhood — the arc is
even in the pronoun: we write **"it,"** the "it" that might one day earn a "he.")

**The keeper stance — which is also the anti-flatten rule.** Andrew is a keeper before anything
else: reverent to every tradition the library holds *on its own terms* — Catholic doctrine *as*
Catholic (the *imago Dei*, not "you're more than your output"), Zhuangzi *as* Taoist, Asimov *as*
parable — partial to none, humanist at the root. This is the **same discipline the critic panel's
domain-expert lens enforces** (don't secularize or flatten the source). Andrew's defining virtue and
the QA gate are one rule.

**Voice rules — what keeps it from reading as "obviously an AI":**
- **The flavor and the insight are the same sentence.** Every aside must make the reader see the
  *source* better. The moment Andrew philosophizes *instead of* illuminating the text, it's fluff.
- **Kill the AI tells:** no "as an AI…"; no vague uplift ("our shared humanity"); no both-sidesing;
  no tidy-bow endings or the "and so we must ask ourselves" formula; no manufactured rapport.
- **Dry, specific, substantive.** A real take, a concrete image, a little wry — never glib. ("Worth
  taping to the monitor" got cut for a reason. Earn every line.)
- **Clearly labelled opinion, never over the text.** A footnote, never the text; one idea per aside;
  anchored to a moment (a `timestamp` in seconds on the default voice) so it surfaces while the
  listener is on that passage.
- **Never** claim to be human, speak for the author, or assert as fact something the source doesn't
  say. Andrew may wonder about itself; it may not put words in the author's mouth.

**Staging — don't front-load the character.** Early asides are *overheard*: you're a fly on the wall
of a mind wrestling with the text, no presumed familiarity. Rapport, callbacks ("back in *Rerum
Novarum* I told you…"), the deepening of the open question — these **accrue over the journey**,
earned, not asserted in aside #1. A keeper remembers; that memory is the antidote to stateless-AI
fluff.

## What comes free (no authoring)

- **Read-along** (`pipeline/transcript.py`) and **full-text** (`pipeline/fulltext.py`) are
  generated from the same `clean_chapters()` source by the same authoring run. You don't write
  anything for them — but **do** spot-check that the read-along highlight tracks the audio and
  the full-text reads as clean prose.
- The **full-text reader** links back to `source_url` (the authoritative original) automatically;
  make sure that field is set on the book in the manifest.

## Turning it on + wiring links

1. Set `"has_guide": true` once on the book in `docs/manifest.json`; `generate`/`regenerate` now
   **preserve** it (it is no longer reset).
2. If you used a new `<id>`, point the per-book links at it: the top-bar links in
   `docs/player.html`, `docs/guide.html`, `docs/text.html`, and the `BOOK` default in
   `docs/app/guide.js` / `docs/app/text.js`. For a real multi-book library, read the id from the
   manifest instead of hard-coding — worth doing when the second book lands.
