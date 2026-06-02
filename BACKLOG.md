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
2. **Laudato si'** — Francis, 2015 (integral ecology; "everything is connected"). ✅ **TEXT SHIPPED**
   — 18 chapters, companion at **HONORS** (12 concepts + 6 Andrew asides + glossary), read-along +
   full-text; in the Queue as a work-in-progress edition. **Audio pending** (overnight / storage-gated;
   voice is Blaine's pick at render time). Dogfooding the playbook on LS fixed three real pipeline
   gaps — plain-`<p>` Vatican layout + an end-matter `<hr>` footnote cut; the text-first no-audio
   commentary timeline; recipe-metadata fallback — and ~22 doc drifts; the plan now matches reality.
   Source: https://www.vatican.va/content/francesco/en/encyclicals/documents/papa-francesco_20150524_enciclica-laudato-si.html

### Laudato Si' — audio render: the no-audio compromises to address (EACH individually)
LS was built **text-first** (no audio). When rendering the audio, work through every item below —
these are the exact shortcuts the no-audio build took, so none should be silently inherited:

1. **Pick + set the voice.** Recipe holds `"voices": ["female"]` only as a *placeholder*. Single
   voice (Blaine delegated the pick to Claude): audition warm candidates — the pastoral tone suits a
   warm voice; lean toward one distinct from the trilogy's Heart/Michael/George — WER+loudness-screen,
   then set the real voice in `data/books/laudato-si.json`.
2. **Render audio** (`audiobook regenerate laudato-si`, *without* `--skip-audio`) — 18 chapters,
   ~4.1h, one single-voice set (~18 MP3s). Confirm it fits the storage cap (Blaine OK'd single-voice LS).
3. **Rebuild the companion against REAL durations.** Commentary `timestamp`s and the concept display
   `timestamp` labels are currently on a *synthesized 155-wpm timeline* (`guide.py` fallback when a book
   has no audio). The full `regenerate` after audio rebuilds the guide from the manifest's real per-voice
   durations. (Concept *fractions* are word-based and already correct; only the seconds-labels +
   commentary placement refine.)
4. **Re-verify + fine-tune commentary placement.** The 6 asides land in ch 1/4/8/9/11/16 on the
   synthesized timeline. After audio, confirm each still sits on its intended passage — especially the
   technocratic-paradigm aside (ch8), the Guardini aside (CH3 anthropocentrism), the conversion aside
   (near the end) — and nudge any timestamp that drifted.
5. **Run audio QA** (`audiobook qa --id laudato-si`): WER ≤0.12, ~−16 LUFS, true-peak <0, no >3s
   silence, duration band. This gate proves audio matches text and was skipped *entirely* text-first.
   Must print **QA PASSED**.
6. **Pronunciation pass.** Listen for Latin/Italian ("Laudato si', mi' Signore", "Franciscus", saints'
   names); add `voices.yaml` lexicon overrides if the TTS mangles them, re-render affected chapters.
7. **Spot-listen** ch1 + a mid-chapter in the *deployed* player ("verify the artifact the user sees");
   confirm the read-along highlight tracks the audio and tap-to-seek lands right.
8. **Promote out of the Queue.** Rendering writes a manifest entry → LS becomes a real library card
   (WIP-badged, like RN). Then **remove LS from the `QUEUE` array in `docs/app/index.js`** (it's no
   longer "pending"), and confirm `has_guide:true` is on its manifest entry so the Companion link shows.
9. **Deploy + verify live** — commit `docs/audio/laudato-si/**` + the updated manifest + rebuilt guide;
   confirm a byte-range request returns **206** (seeking) on the live MP3s.

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
- **How to organize the growing library + Audiobook Queue** (open question — settle before it gets
  big). Axes on the table: **chronological** (c. 300 BC → 2026, the through-time story), **by theme**
  (work & dignity / machines & the mind / the human person), **by "rabbit hole"** (the citation trail
  you followed to get here — Magnifica → its sources → theirs), or **by tag** (multi-axis: tradition,
  era, thread, medium). Leaning: a **tag-based model** underneath with **chronological** and
  **thread** as the two default *views*, so the same library re-sorts instead of forcing one
  hierarchy. The Queue section is the first surface that will feel this.
- **Track the citation/influence thread as data** ("feels like they all tie together"). Each
  edition records what it *references*, tagged **direct** (the work explicitly cites it — Magnifica
  → Augustine, Arendt, Guardini, the UDHR…) vs. **supplemental** (a parent/kin it descends from but
  doesn't name). That graph powers a "pull the thread" view — *what this text draws on* and *what
  draws on it* — plus the timeline/graph and the concept links below. WORK-QUEUE Thread 1 already
  traces Magnifica's real citations in prose; promote it to a per-book `references: [{id, type,
  note}]` field so the UI can render it. **Seed data is already in hand:** a book's own footnotes
  are its *direct* references — Laudato Si's ~170 (now stripped from narration by the end-matter
  `<hr>` cut) name **Guardini's *The End of the Modern World*** (shared with Magnifica!), the CST
  chain, Aquinas, Basil, Dante. Harvest the end-matter we cut from the audio rather than discarding
  it — noise for narration, signal for the graph.
- **Cross-edition concept links** — when concept cards in different books name the same idea
  (subsidiarity, the dignity of work, the common good), link them across editions. The data is
  already there; it just isn't wired between books yet.
- **Search / "find a passage"** across a book's full text (and eventually across the library).
- **Shareable deep-links with a preview** — a concept or passage URL that unfurls a title/quote
  card (Open Graph tags) when shared.
- **Accessibility deepening** — a full screen-reader/keyboard audit, prefers-reduced-motion,
  high-contrast pass; partly done, worth a dedicated sweep.
- ~~**A stated persona for the AI commentator — "the voice in the margin."**~~ ✅ **SHIPPED as
  Andrew.** The director's-commentary voice is now a named character — **Andrew** (after Asimov's
  Bicentennial Man) — introduced on the about page (`about.html#andrew`) and named in the companion
  UI. The original principle held (*a declared thing is more honest than a hidden default*), but the
  earlier "**never invent the eye**" hard line was deliberately superseded: a *covert* persona would
  be the dishonest move, but a **declared, human-authored, fenced fiction** applies the same
  principle one level up — the about page tells the truth about the *making*, leaving only the
  character's *being* an open question in-world. Full **persona charter** in
  `docs/playbook/companion-authoring.md` + a humanist-lens check in `docs/playbook/critic-panel.md`.
  Still pairs with the voiced-commentary track below (a spoken voice will want Andrew most).

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

## Hosting & sustainability (the audio-bandwidth upgrade path)

**Current state (do nothing yet):** site + MP3s both on **GitHub Pages**. The player already
lazy-loads (`<audio preload="metadata">`, one chapter loaded only when played, HTTP range/206 for
seeking), so a browse costs ~0 and a one-chapter listen ~3 MB — not the whole 40–104 MB book. We
sit far under GitHub Pages' **100 GB/month soft bandwidth** limit (soft = throttle + a polite email
suggesting a CDN, *not* a surprise bill). **The wall we hit first is storage, not bandwidth:**
GitHub Pages caps a published site at **~1 GB**, and `docs/audio/` is already ~258 MB across 2
books.

**Trigger to migrate:** when the repo's `docs/audio/` approaches **~700 MB** (≈ the 3rd–4th book),
or GitHub emails about bandwidth. Not before — we're nowhere near it.

### Audio is now a BUILD ARTIFACT (this reframes the whole backup/storage question)

Every book is reproducible from git alone via a tracked **recipe** — so MP3s and companion JSON
are *build outputs*, not precious snapshots from a particular session. Built this turn:
- **`data/books/<id>.json`** — the complete declarative build input per book (title, author, voices,
  `source_file`, `source_url`, `rights`, `chapter_map`, `repairs`, `guide_builder`, `wip`). Nothing
  lives only in shell/LLM history anymore.
- **`data/sources/<id>.html`** — the **committed source-text snapshot** (508 KB for both books).
  This is the canonical text: regeneration reads it, so builds are **offline, byte-stable, and
  independent of vatican.va** (the live page can drift or 404 — we don't care). `source_url` stays
  as the attribution reference.
- **`audiobook regenerate <id>`** — rebuilds a book end-to-end from its recipe (resumable;
  `--skip-audio` for text/companion only). Verified: text output is **byte-identical across runs**.
- Recipe-integrity test (`test_recipes.py`) guards that every recipe is complete and its referenced
  files exist — so "regenerate" can't silently rot.

**Honest caveat:** the *text/companion* layer is deterministic; the **MP3s are reproducible-in-
spirit, not bit-identical** — Kokoro/ffmpeg produce equivalent, QA-passing audio each run, not the
same bytes. So "regenerate" means "produce a fresh good edition," which is exactly what we want.

**This answers the three questions that prompted it:**
- *"git rule to purge old MP3s from history, keep only the newest?"* — **Not needed, and we
  shouldn't.** Rewriting history on every render is fragile (breaks clones/forks, append-only by
  design). Instead: once hosting moves off Pages, **stop committing MP3s at all** (add
  `docs/audio/**/*.mp3` to `.gitignore`) — they become regenerable artifacts hosted on R2. The
  recipe + source snapshot (tiny, text) is what's version-controlled.
- *"keep book 1, ignore the rest after Cloudflare?"* — **No need to pick.** Keep *all recipes*
  (kilobytes), zero MP3s. Nothing arbitrary.
- *"scripts that always regenerate MP3s cleanly?"* — **Done** (`regenerate`). The one gap to close
  for full from-scratch reproducibility: a `setup_models.py` run fetches the Kokoro model (already
  scripted, ~325 MB, not in git — correct, it's a dependency not a source).

**At migration, the `.gitignore` move:** today MP3s are *served from* `docs/audio/` so they must
stay committed (ignoring them would 404 the live site). Once `audio_base` points at R2, the site no
longer needs them in-repo → then add the gitignore rule and `git rm --cached` them. Optionally purge
history with `git-filter-repo`/BFG at that point to shrink `.git` (currently ~405 MB, mostly old MP3
blobs). Until then, GitHub remains a fine 3rd backup (laptop + GitHub + history).

**The plan: move MP3s + covers to Cloudflare R2 (S3-compatible object store), keep the site +
manifest on GitHub Pages.** Why R2: **egress (bandwidth) is always $0**, so the bill is decoupled
from audience size. Storage: first **10 GB free**, then **$0.015/GB-month** — i.e. 20 GB = **$0.15/mo**,
50 GB = $0.60, 100 GB = $1.35. R2 supports range requests (seeking keeps working). The catch with
"free egress" (asked + answered): it's Cloudflare's deliberate anti-AWS-lock-in loss-leader, not
magic — what *is* metered is **operations** (1M writes + 10M reads/mo free, then cheap) and
**storage**, plus a **credit card on file** (set a billing alert). A few large, lazily-loaded files
is the ideal low-op case, so none of that bites us. R2 being S3-compatible is the hedge if the deal
ever changes.

**Accommodation already built (so migration is a config flip, not a code change):** the manifest
supports an optional top-level **`audio_base`**; `logic.resolveAsset(base, path)` prepends it to
audio + cover paths, and player/index use it. **Absent today → paths stay relative → current
behavior exactly** (verified: no `audio_base` in the manifest). Covered by unit tests
(`resolveAsset`, `audioBase` surfacing).

**Migration runbook (when triggered):**
1. Create a Cloudflare account + R2 bucket; upload `docs/audio/**` preserving paths
   (`audio/<book>/<voice>/chapter-NN.mp3`, plus `cover.svg`).
2. Attach a **custom domain** to the bucket (e.g. `audio.<site>`) — the `r2.dev` URL is
   rate-limited/dev-only; the custom domain routes through Cloudflare's cache + honors Range.
3. Set a **CORS** rule allowing the site origin (`GET, HEAD`; expose `Content-Length`,
   `Content-Range`, `Accept-Ranges`). Don't enable Brotli/gzip on `audio/mpeg` (breaks 206 seeking).
4. Set `"audio_base": "https://audio.<site>"` at the manifest top level. Done — the player resolves
   everything there.
5. Verify seeking returns 206 in devtools; then `git rm docs/audio/**` to drop the repo back under
   the 1 GB Pages limit (keep the R2 copy; optionally mirror the **public-domain** titles to
   Internet Archive as a free backup — verify rights before posting the in-copyright 2026 text).

**Alternatives considered:** Backblaze B2 + Cloudflare (also $0 egress via Bandwidth Alliance;
more wiring) · Internet Archive (free, mission-aligned — good *secondary mirror* for PD titles) ·
**avoid** Netlify/Vercel for media (both cap bandwidth *harder* than GitHub and Vercel Hobby bars
non-personal use) · Cloudflare Stream is per-minute video pricing, overkill.

**Donations / "costs only" — decision: take nothing for now.** With R2 the hosting bill is ~$0–$2/mo,
and the overhead of accepting money (it's personal *taxable* income with no legal "costs-only"
guarantee unless you set up a fiscal sponsor / 501(c)(3)) dwarfs the cost. For a free site of
religious + non-commercially-permissioned texts (the Vatican permission is *non-commercial*), a tip
jar paying a person also reads like monetization — best avoided. **If costs ever become real:** the
cleanest low-overhead path is **Liberapay** (non-profit, no platform cut) with a plain "donations
only offset hosting; the project never profits" note; the *provable* costs-only path is **Open
Collective** + a fiscal host (public budget showing money-in = invoice-paid, surplus $0 — note the
general-purpose Open Collective Foundation closed end of 2024, so a host would need shopping). A
formal 501(c)(3) only if it ever becomes substantial. Keep surplus at $0; never offer donor perks
(that converts a "gift" into a taxable exchange *and* muddies the non-commercial framing).

## Still in scope NOW (no new MP3s)
- Tier 2: generic `audiobook generate <url>` generator + README.
- Tier 3 companion medium as **text/JSON/HTML**: concept cards, grounded study guide,
  glossary, verified further-reading, and **director's commentary as timestamp-anchored
  TEXT footnotes** (no audio). All generated offline into static files.

When ready to build the deferred audio, free disk first, then generate into the existing
`editions` structure (player already designed to switch editions/voices via the manifest).
