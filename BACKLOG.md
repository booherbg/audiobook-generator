# Backlog (deferred for storage reasons)

The local disk is tight, so audio generation is capped at the **core set** only:
the 34 MP3s of *Magnifica Humanitas* (17 chapters × 2 voices).

**Do NOT generate additional MP3s** beyond the core set without explicit go-ahead.

## Deferred (audio-heavy) — build later when storage allows
- **Voiced director's-commentary track** — a separate spoken commentary audio set.
- **Enriched "woven" edition** — an alternate full audiobook with commentary spliced
  into the narration at chapter breaks (another ~full audio set per voice).
- **Additional books** (sci-fi, PDFs) — each is its own audio set.

## Still in scope NOW (no new MP3s)
- Tier 2: generic `audiobook generate <url>` generator + README.
- Tier 3 companion medium as **text/JSON/HTML**: concept cards, grounded study guide,
  glossary, verified further-reading, and **director's commentary as timestamp-anchored
  TEXT footnotes** (no audio). All generated offline into static files.

When ready to build the deferred audio, free disk first, then generate into the existing
`editions` structure (player already designed to switch editions/voices via the manifest).
