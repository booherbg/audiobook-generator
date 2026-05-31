# Backlog (deferred for storage reasons)

The local disk is tight, so audio generation is capped at the **core set** only:
the 34 MP3s of *Magnifica Humanitas* (17 chapters × 2 voices).

**Do NOT generate additional MP3s** beyond the core set without explicit go-ahead.

## Deferred (audio-heavy) — build later when storage allows
- **Voiced director's-commentary track** — a separate spoken commentary audio set.
- **Enriched "woven" edition** — an alternate full audiobook with commentary spliced
  into the narration at chapter breaks (another ~full audio set per voice).
- **Additional books** (sci-fi, PDFs) — each is its own audio set.

## Next big build: the two pillar documents (same full treatment)
*Magnifica Humanitas* explicitly stands on two prior encyclicals; give each the SAME
end-to-end treatment we built here (audiobook + read-along transcript + full-text reader +
grounded companion with director's commentary), so the three form a small connected library.

1. **Rerum Novarum** — Leo XIII, 1891 (labour & capital; the origin of Catholic Social
   Teaching, whose 135th anniversary this encyclical marks).
   Source: https://www.vatican.va/content/leo-xiii/en/encyclicals/documents/hf_l-xiii_enc_15051891_rerum-novarum.html
2. **Laudato si'** — Francis, 2015 (integral ecology; "everything is connected").
   Source: https://www.vatican.va/content/francesco/en/encyclicals/documents/papa-francesco_20150524_enciclica-laudato-si.html

**Method (reuse the pipeline — it's already generic):**
- `audiobook generate <url> --id <id> --title ... --author ...` → chaptered MP3s + manifest
  (resumable, multi-voice). Audio QA via `build/qa_run.py`. (Storage-gated — see cap above.)
- Read-along + full-text reader come free: `pipeline.transcript` + `pipeline.fulltext` run off
  the same load→clean→chunk source (`pipeline.source_text`). Player/guide/text pages are
  manifest-driven, so a new book id slots in.
- Companion: clone `pipeline/build_guide_magnifica.py` → `build_guide_<id>.py` with that
  document's concepts/anchors/commentary/glossary. **Honor the original**: quotes EXTRACTED
  VERBATIM (anchors must be exact substrings of the source), deep-links voice-independent
  ({chapter, fraction}), commentary clearly-labelled AI opinion in the Asimov/Pratchett/
  Stephenson/ancients register, reverent to the text.
- **Run the critic panel before shipping** each: educator + humanist + mystical/church-historian
  read the companion AGAINST the source; iterate to a HONORS verdict. (Verbatim quoting is
  necessary but NOT sufficient — blurbs can still secularize/flatten the original's claims.)
- Cross-link the three: "further reading" + the existing concept references already point at
  RN and Laudato si'; once they exist as books, make those live links between editions.

## Still in scope NOW (no new MP3s)
- Tier 2: generic `audiobook generate <url>` generator + README.
- Tier 3 companion medium as **text/JSON/HTML**: concept cards, grounded study guide,
  glossary, verified further-reading, and **director's commentary as timestamp-anchored
  TEXT footnotes** (no audio). All generated offline into static files.

When ready to build the deferred audio, free disk first, then generate into the existing
`editions` structure (player already designed to switch editions/voices via the manifest).
