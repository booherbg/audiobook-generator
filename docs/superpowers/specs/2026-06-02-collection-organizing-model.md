# Collection organizing model — the map (rooms · trail · timeline)

*Status: design spec, backlogged. The model is settled; the matrix-view UI is future work.
Authored 2026-06-02. Answers the open "how do we organize the growing library" question in
[BACKLOG.md](../../../BACKLOG.md).*

## The problem
The library is outgrowing a flat list (Magnifica · Rerum Novarum · Laudato Si', plus a queue of CST,
the ancients, world-wisdom, and public-domain sci-fi). It needs an organization that **orients the
casual reader without confusing them, and rewards the curious one with a trail to follow** — and
that holds the Western and Eastern threads in honest conversation, not a flattened "it's all one."

## The shape: a matrix, not a line
Two axes:
- **Three rooms (the questions / pillars):** **Humanism** (what is owed to the person?),
  **Technology** (what does the machine do to us?), **Consciousness** (what, underneath, are we?).
- **Three traditions (the lenses):** **West** (the ethics of the person — CST, the ancients, the
  apophatic mystics), **East** (the metaphysics of the self — the Upanishads, Zhuangzi, the
  Dhammapada, the Ashtavakra Gita), **Modern** (secular — the UDHR, the public-domain sci-fi,
  science cited but unhosted).

Every work sits at an intersection. **Humanism leans West; Consciousness leans East; Technology is
the shared room where all three traditions meet — and where AI lives.** The centerpiece (Magnifica)
sits in Technology; the journey radiates out from it and rejoins at *what is irreducibly a someone?*

## Tags (the data under the views)
Each work carries flat tags: one or more **pillars** (`humanism` `technology` `consciousness`), one
**tradition** (`west` `east` `modern`), and an optional **form** flag (`fiction` for the narrative
on-ramps). Tags live on the queue items today (`docs/app/index.js` `QUEUE`); the manifest books
should be tagged to match. **The views are re-sorts of this one tagged set — not separate hierarchies.**

## Three views over the one set
1. **Rooms (default):** grouped by pillar. A casual visitor picks a room and finds a few works, each
   with a title, a length, and a one-line "what this is." In each room the traditions answer side by side.
2. **Trail (the rabbit hole):** the citation/influence path — Magnifica → its sources → theirs — plus
   cross-room kinship. The curious reader's thread (see "the trail" below).
3. **Timeline:** chronological (c. 500 BCE → 2026), **honest about disputed dates** (the Ashtavakra
   Gita shows a range — c. 500 BCE–14th c. CE — not a fake pin).

## Three design rules
- **Progressive disclosure** — clarity at rest, depth on demand. The surface is clean and
  casual-friendly; every work carries an opt-in "pull the thread." Nobody is confused; the curious
  never dead-end.
- **Sci-fi as on-ramps** — the fiction is the low-friction door (you can *enjoy* Erewhon in an
  afternoon). Each pairs with the heavy text it lights up (The Machine Stops ↔ the technocratic
  paradigm; Erewhon ↔ machine-consciousness). Host the public-domain ones; link out the rest.
  Tagged `fiction` so a "start here, it's a good read" entry is possible.

## Three curation laws
- **Cohesive** — no islands. Every work links to at least one other (the trail + the matrix). The
  through-line is the spine; the rooms are the cross-section.
- **Respectful** — each tradition in its own voice. The rooms are **dialogues, not unisons.** The
  Consciousness room is the proof: the Upanishads say *eternal Self*; the Dhammapada says *no-self*;
  the Cloud of Unknowing says *union with God*; the sci-fi asks *is anyone home at all* — four
  answers, one question. Never flatten to "the same thing."
- **Non-redundant** — every work earns a **distinct slot.** Test before queuing: does it bring
  something no other work does? If two do the same job, cut one or link out. (The non-dual trio
  passed: witness-Self / radical directness / no-self.)

## The trail (what does the pulling)
Each work ends with **"where this leads"**: forward (what cites it), back (what it draws on), across
(its room-mates that disagree). This single mechanism satisfies "don't confuse anyone / let the
curious go deep" — the casual reader never has to look; the curious one always has a next thread. It
needs a per-work `references: [{id, type: direct|kin, note}]` field (the citation-graph idea already
in the backlog).

## Worked example — the Consciousness room
Upanishads (Katha + Mundaka) · Ashtavakra Gita · Dhammapada *[East]* · The Cloud of Unknowing
*[West]*, with **Schrödinger** and **Bill East** as cited-not-hosted modern voices. Four traditions,
one question, four genuinely different answers. The companion ("Andrew") is load-bearing here — it
is the wire from these ancient texts to Magnifica's AI age, not a margin note.

## Status / build order (when picked up)
1. Tag the manifest books to match the queue's `tags`.
2. Add the per-work `references` field; seed it from the companions' existing cross-links + the
   queue notes.
3. The three views as re-sorts on the library page: **Rooms** (default) with **Trail** and
   **Timeline** as toggles; the per-work "pull the thread" panel.

Until then the tags are inert metadata and the library stays a flat (but length-labeled) list — no
regression, purely additive.
