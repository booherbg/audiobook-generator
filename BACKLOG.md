# Backlog (deferred for storage reasons)

The local disk is tight, so audio generation is capped at the **core set** only:
the 34 MP3s of *Magnifica Humanitas* (17 chapters × 2 voices).

**Do NOT generate additional MP3s** beyond the core set without explicit go-ahead.

## Deferred (audio-heavy) — build later when storage allows
- **Voiced director's-commentary track** — a separate spoken commentary audio set.
- **Enriched "woven" edition** — an alternate full audiobook with commentary spliced
  into the narration at chapter breaks (another ~full audio set per voice).
- **Additional books** (sci-fi, PDFs) — each is its own audio set.

## Deferred (UX) — "listen while you read" / continuous playback
The companion and full-text live on separate HTML pages; navigating to them stops the
audio (the `<audio>` element is destroyed on page load). Two tiers were scoped:
- **Sticky mini-player (beta).** A mini bar on guide/text pages sharing the main player's
  resume state; concept "listen" links seek IN-PAGE instead of navigating away. The one
  seam: navigating *from* the player pauses audio for a single tap to resume (browsers
  can't carry a playing element across a page load). Clean-ish; deferred for now.
- **Seamless SPA player (the real fix).** Convert the companion + full-text into in-page
  panels over a single persistent player so audio never stops — "SoundCloud-style." This
  is a genuine architecture change (one page, swap panels, route via history API) and the
  right long-term home for continuous playback. Revisit together.

## Next big build: the two pillar documents (same full treatment)
*Magnifica Humanitas* explicitly stands on two prior encyclicals; give each the SAME
end-to-end treatment we built here (audiobook + read-along transcript + full-text reader +
grounded companion with director's commentary), so the three form a small connected library.

> **Follow the playbook:** [docs/playbook/README.md](docs/playbook/README.md) is the pull-and-go
> runbook for this; the contract is [the expansion spec](docs/superpowers/specs/2026-05-31-book-expansion-spec.md).
> The method below is the summary; the playbook has the exact commands, prompts, and gates.

1. ~~**Rerum Novarum** — Leo XIII, 1891~~ ✅ **SHIPPED** (single British voice "George", 13
   chapters, companion at HONORS, on the library as a work-in-progress edition).
2. **Laudato si'** — Francis, 2015 (integral ecology; "everything is connected").
   Source: https://www.vatican.va/content/francesco/en/encyclicals/documents/papa-francesco_20150524_enciclica-laudato-si.html
   — The obvious next book: completes the trilogy, the companions already cross-link to it,
   and the pipeline is now proven on two very different source layouts.

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

## Other bodies of work to consider (idea bank)

Captured for later — not committed. Grouped by what they'd grow. Each new *book* is its own
audio set, so all are storage-gated; the text/companion layer of any of them can ship audio-free.

> **→ The full, copyright-vetted reading list is now [docs/WORK-QUEUE.md](docs/WORK-QUEUE.md).**
> It traces Magnifica's references back through the CST lineage → philosophy of technology →
> the ancients (main thread + offshoots), plus two wider runs: world wisdom traditions
> (Zhuangzi's "machine heart", the Golem, the Gita's karma-yoga) and public-domain sci-fi /
> free manifestos (Erewhon, R.U.R., The Machine Stops, Kevin Kelly's *Out of Control*). Every
> item carries a copyright verdict. The summary below is the short version.

**More texts — the natural neighbours.**
- **Complete the CST arc:** *Quadragesimo Anno* (Pius XI, 1931, names subsidiarity), *Pacem in
  Terris* (John XIII, 1963), *Populorum Progressio* (Paul VI, 1967), *Laborem Exercens* /
  *Centesimus Annus* (JP II). With RN + Laudato si' + Magnifica, this becomes a real, navigable
  library of the whole tradition — and the companions already gesture at these links.
- **The ancients Magnifica cites:** *City of God* Bk. XIV (Augustine — the literal source of the
  Babel/two-cities image), Aristotle's *Ethics*/*Politics*, Aquinas excerpts — all public-domain
  (use the named PD translations in the work queue). Plus the **UDHR** (1948, free, explicitly cited).
- **World wisdom run** (secondary): Zhuangzi, the Golem sources, the Bhagavad Gita on work — see
  the work queue, which separates grounded primary texts from debunked pseudo-history (Vimanas).
- **Public-domain literature / sci-fi** (the user's original "old scifi books"): start with
  *Erewhon* / *The Machine Stops* / *R.U.R.* / *Frankenstein* — all PD, all on-theme.

**Deepen the experience (mostly text/JS — cheap, no new audio).**
- **A library landing that shows the connections** — the three encyclicals as a small annotated
  timeline/graph (1891 → 2015 → 2026), since the ideas literally descend from each other.
- **Cross-edition concept links** — when concept cards in different books name the same idea
  (subsidiarity, the dignity of work, the common good), link them across editions. The data is
  already there; it just isn't wired between books yet.
- **Search / "find a passage"** across a book's full text (and eventually across the library).
- **Shareable deep-links with a preview** — a concept or passage URL that unfurls a title/quote
  card (Open Graph tags) when shared.
- **Accessibility deepening** — a full screen-reader/keyboard audit, prefers-reduced-motion,
  high-contrast pass; partly done, worth a dedicated sweep.
- **A stated persona for the AI commentator — "the voice in the margin."** Right now the
  director's-commentary's only anchor is "btw this is an AI." Proposal: give it a *declared lens*
  — a Stoic-humanist reader in the register of Montaigne + Marcus Aurelius, with the deep-time
  sensibility of Stephenson/Sagan/Le Guin, Asimov's "the laws are about the humans who wrote
  them," and a low simmer of Pratchett. **Principle: a declared lens is MORE honest than a hidden
  default** — it converts an invisible training-set bias into a disclosed one the reader can
  calibrate against, exactly as verbatim quotes let them check the author. **Hard line: the voice
  may describe the lens it looks through; it may NEVER invent the eye** — no fabricated name,
  biography, body, or feelings (that's the "AI pretending to be something it's not" failure the
  project avoids). Two rationed *moves* in its repertoire: the true "I am one of the new things
  these texts worried about" reflex, and a Socratic closing question. Encode as a **persona
  charter** in `docs/playbook/companion-authoring.md` (replacing the lineage-only persona note)
  + a one-line check in the critic panel's humanist lens, so persona-drift and the dishonest-
  backstory failure become things the HONORS gate catches. Pairs with the voiced-commentary track
  below (a spoken voice needs a coherent persona most). Text/playbook change, zero new audio.

**Audio-layer ambitions (storage- and time-gated — revisit deliberately).**
- The **voiced director's-commentary track** and the **woven "enriched" edition** (already
  above) — both want the continuous-play SPA player to land first.
- **A second voice for Rerum Novarum** (currently single-voice "George") once storage allows,
  so it matches Magnifica's choose-your-narrator parity.
- **Chapter-level "listen in <language>"** once multilingual audio exists.

**Harden the tooling (so the above is cheap and safe).**
- **PDF loader** — `pipeline/load.py:PDFLoader` is a stub (`spec §20`); needed for the
  public-domain books that only exist as PDF/scans, and the user's original ask.
- **Private/password-gated editions** — the user flagged early that future private books should
  be protectable; not built. (Static-site auth is limited; scope it honestly — likely a simple
  gate, not real security.)
- **A real CI run** of `pytest` + `node --test` + `validate_guide` on push, so regressions in a
  growing library are caught automatically rather than by hand.
- **An LLM copy-edit pass as a documented step** — the "R esponsibility / arid motive / Apostle
  saith" class of OCR/export defects can only be caught by a careful reader, not a script. Bake
  the proofread-against-source critic into the playbook's per-book checklist.

## Still in scope NOW (no new MP3s)
- Tier 2: generic `audiobook generate <url>` generator + README.
- Tier 3 companion medium as **text/JSON/HTML**: concept cards, grounded study guide,
  glossary, verified further-reading, and **director's commentary as timestamp-anchored
  TEXT footnotes** (no audio). All generated offline into static files.

When ready to build the deferred audio, free disk first, then generate into the existing
`editions` structure (player already designed to switch editions/voices via the manifest).
