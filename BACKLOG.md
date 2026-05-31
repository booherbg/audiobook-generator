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

> **Follow the playbook:** [docs/playbook/README.md](docs/playbook/README.md) is the pull-and-go
> runbook for this; the contract is [the expansion spec](docs/superpowers/specs/2026-05-31-book-expansion-spec.md).
> The method below is the summary; the playbook has the exact commands, prompts, and gates.

1. **Rerum Novarum** — Leo XIII, 1891 (labour & capital; the origin of Catholic Social
   Teaching, whose 135th anniversary this encyclical marks).
   Source: https://www.vatican.va/content/leo-xiii/en/encyclicals/documents/hf_l-xiii_enc_15051891_rerum-novarum.html
2. **Laudato si'** — Francis, 2015 (integral ecology; "everything is connected").
   Source: https://www.vatican.va/content/francesco/en/encyclicals/documents/papa-francesco_20150524_enciclica-laudato-si.html

**Method (reuse the pipeline — it's already generic):**
- `audiobook generate <url> --id <id> --title ... --author ...` → chaptered MP3s + manifest
  (resumable, multi-voice). Audio QA via `audiobook qa --id <id>`. (Storage-gated — see cap above.)
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

## Stretch: multilingual editions (e.g. Spanish) — NEAT, and very feasible
The same encyclical in other languages — Spanish first. This fits the mission beautifully
(wider reach, same craft) and the pipeline is most of the way there already.

**Why it honors the original:** we do **NOT** machine-translate. The Vatican publishes its own
**official translations**, so a Spanish edition uses the authoritative Spanish text as its source
(swap the `/en/` URL for `/es/`). Verbatim quotes then extract from the Spanish source exactly as
they do from the English — the no-hallucination guarantee carries over unchanged.

**What already works:**
- **Voices.** Our installed Kokoro model ships multilingual voices — Spanish `ef_dora` (f),
  `em_alex` / `em_santa` (m); also Italian (`if_sara`, `im_nicola`) and Portuguese (`pf_dora`,
  `pm_alex`). So the two-voice (female/male) model holds for ES/IT/PT. (French ships only one
  voice, `ff_siwis` — single-voice edition there.) `espeak-ng` (already a dependency) phonemizes
  all of these.
- **Text → read-along → full-text → player** are language-agnostic: they run off
  `source_text.clean_chapters()` and the manifest, so a Spanish source flows through untouched.

**Real work to do (honest list):**
1. **Un-hardcode the language.** `pipeline/tts.py:23` passes `lang="en-us"`; make it per-book /
   per-voice (e.g. `es` for Spanish voices). Small, central change.
2. **Per-language normalization.** `pipeline/normalize.py` expands numbers/abbreviations in
   English; Spanish needs its own (números a palabras, etc.) and a Spanish `lexicon` in
   `voices.yaml`. Audition + tune by ear like we did for English.
3. **Companion authored in-language.** Blurbs/commentary/glossary rewritten in Spanish (quotes
   auto-extract from the Spanish source). Run the **critic panel with Spanish-reading lenses**
   (e.g. educador, humanista, historiador/teólogo) to a HONORS verdict — same gate, in Spanish.
4. **Player UI i18n (optional, nice).** Chrome strings ("Voice", "Companion", "Full text",
   "listen to this chapter") are English; localize per edition for polish. Content works without it.
5. **Library/voice labels** per language; cross-link language editions of the same work.

**Storage:** each language is a full audio set — **audio-heavy, so gated by the cap above.** The
*text* experience (read-along + full-text + companion) can ship in Spanish with **zero new audio**,
which is a great low-cost first slice to prove the path.

**First slice suggestion:** Spanish *Magnifica Humanitas*, text-only (no audio) — proves source
swap + Spanish companion + Spanish critic panel; add the audio later when storage allows.

## Still in scope NOW (no new MP3s)
- Tier 2: generic `audiobook generate <url>` generator + README.
- Tier 3 companion medium as **text/JSON/HTML**: concept cards, grounded study guide,
  glossary, verified further-reading, and **director's commentary as timestamp-anchored
  TEXT footnotes** (no audio). All generated offline into static files.

When ready to build the deferred audio, free disk first, then generate into the existing
`editions` structure (player already designed to switch editions/voices via the manifest).
