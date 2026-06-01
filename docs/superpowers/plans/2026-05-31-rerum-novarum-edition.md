# Rerum Novarum Edition — Implementation Plan

> **For agentic workers:** execute task-by-task; steps use `- [ ]` checkboxes. This is an
> autonomous goal-mode run: build the edition, then loop the QA + critic audit until the
> **history and mystical/theology critics are satisfied (HONORS)** and **all tests pass**.
> Pause around 07:30 CDT. Follow [the playbook](../../playbook/README.md).

**Goal:** Add *Rerum Novarum* (Leo XIII, 1891) as a complete edition — single distinctive
(British) voice audiobook + read-along + full-text + a world-class, source-honoring companion —
hidden on the library index behind a Shift-to-reveal "work in progress" gate.

**Architecture:** Reuse the existing pipeline. RN has no usable headings, so introduce a generic,
tested **chapter-map** mechanism (curated `{title, anchor}` list → sections) used identically by
audio generation and by the text-derived artifacts, so on-screen always matches spoken. Lightly
refactor three single-book assumptions (`guide.py` `books[0]`, hardcoded nav links, index render)
to support a real multi-book library.

**Tech stack:** unchanged — Python 3.12 / uv / Kokoro ONNX / ffmpeg / vanilla JS / pytest +
node:test / `gh` → Pages. New voice from the installed multilingual Kokoro model.

**Scope decisions (from the user):**
- **Audio:** single voice, my pick, "keep it fun" → a **British male** voice (fitting for an 1891
  encyclical; audition `bm_george` / `bm_lewis` / `bm_daniel` and pick by ear). One voice = ~10–12
  MP3s, within reason; confirm disk headroom first.
- **Index:** RN is a WIP — hidden by default, revealed by **holding Shift** on the library page.
- **Chaptering:** curated by an English-history-educator lens, then validated in the critic loop.

---

## Chapter map (educator's thematic breakdown)

RN is ~64 numbered paragraphs (Vatican HTML ≈ 115 cleaned paragraphs, ~14.4k words). Channeling an
English-history educator, break the argument into **~11 listenable chapters (~8–10 min each)** that
follow Leo XIII's actual structure: the problem → the false remedy (socialism) → property &
family → the Church & the classes → duties & dignity → the State → wage & ownership →
association → close. Final titles/anchors pinned to **verbatim** phrases in Phase 2.

1. **The Spirit of Revolutionary Change** — the social question; the misery of the working class.
2. **The False Remedy of Socialism** — abolishing property would rob the worker it claims to help.
3. **Property and the Natural Law** — reason, foresight, the fruits of labor; man is not the beast.
4. **The Family Before the State** — domestic society precedes the commonwealth; against intrusion.
5. **Neither Class the Enemy of the Other** — the Church enters; capital and labor need each other.
6. **The Dignity of Work and the Truth About Wealth** — mutual duties; labor's dignity; rich & poor before God.
7. **What the Church Brings** — her real remedies; charity beyond almsgiving; her institutions.
8. **The Duty of the State to the Worker** — common good, distributive justice, special care for the poor.
9. **Just Limits: Rest, Hours, and the Vulnerable** — bounds of state power; Sunday rest; women & children.
10. **A Living Wage and the Hope of Ownership** — the famous just-wage passage; workers becoming owners.
11. **The Right to Associate, and a Closing Appeal** — unions & the guild echo; Catholic societies; charity.

(10–12 is acceptable; the history/educator critic finalizes the count and the boundaries.)

---

## Task 0 — Light multi-book refactor (do first; unblocks everything)

**Files:** `pipeline/guide.py`, `docs/app/player.js`, `docs/app/guide.js`, `docs/app/text.js`,
`docs/player.html`, `docs/guide.html`, `docs/text.html`, `docs/tests/test_logic.mjs` (or a new test).

- [ ] **guide.py:** make `_voice_timeline` / `_default_voice` look the book up **by id**, not
  `books[0]`. Thread `book_id` in from `build_guide`. Add a regression note.
- [ ] **Nav links book-aware:** in `player.js`, set both `#companion-link` and `#text-link` hrefs
  from `vm.id` (companion already dynamic; add text). In `guide.js` / `text.js`, set the `‹ Player`
  and `Full text`/`Companion` top-bar hrefs from `BOOK`. Remove reliance on the hardcoded
  `?book=magnifica-humanitas` in the three HTML files (keep as harmless default only).
- [ ] **Verify:** `node --test docs/tests/*.mjs` green; existing Magnifica links still resolve.
- [ ] **Commit:** `refactor: make companion/timeline/nav book-aware (multi-book library)`.

## Task 1 — Chapter-map mechanism (generic, tested)

**Files:** create `pipeline/chapter_map.py`, `pipeline/tests/test_chapter_map.py`; modify
`pipeline/source_text.py` and `pipeline/__main__.py` (generate + qa).

- [ ] **Write the failing test** `test_chapter_map.py`: given a Document of one section with
  paragraphs `["…A…","…B…","…C…","…D…"]` and map `[{title:"One",anchor:"A"},{title:"Two",anchor:"C"}]`,
  `resection(doc, map)` returns 2 sections titled One/Two with paragraphs `[A,B]` and `[C,D]`.
- [ ] **Implement `pipeline/chapter_map.py`:**
  ```python
  def load_map(path): return json.loads(Path(path).read_text())  # [{"title","anchor"}]
  def resection(doc, chapter_map):
      paras = [p for sec in doc.sections for p in sec.paragraphs]
      # find first paragraph index at/after the cursor containing each anchor (case-insensitive)
      starts, cur = [], 0
      for ch in chapter_map:
          a = ch["anchor"].lower()
          i = next((k for k in range(cur, len(paras)) if a in paras[k].lower()), None)
          if i is None: raise ValueError(f"anchor not found: {ch['anchor']!r}")
          starts.append(i); cur = i + 1
      secs = []
      for n,(ch,s) in enumerate(zip(chapter_map, starts)):
          e = starts[n+1] if n+1 < len(starts) else len(paras)
          body = paras[:e] if n==0 else paras[s:e]   # pre-first-anchor front matter → ch1
          secs.append(Section(ch["title"], body))
      doc.sections = secs
      return doc
  ```
- [ ] **Thread it through both call sites** so audio and text stay identical:
  - `source_text.clean_chapters(resource, chapter_map=None)` → resection after cleaning, before
    `chunk_document`.
  - `generate` / `qa` in `__main__.py`: add `--chapter-map FILE`; apply the same resection after
    `clean_document`, before `chunk_document`.
- [ ] **Verify:** new test passes; full `pytest` green.
- [ ] **Commit:** `feat: chapter-map resectioning for texts without usable headings`.

## Task 2 — Pin the RN chapter map to verbatim anchors

**Files:** create `data/chapter_maps/rerum-novarum.json` (tracked); `build/rerum-novarum.html` (cached, gitignored).

- [ ] Dump cleaned RN paragraphs (`clean_chapters("build/rerum-novarum.html")` with no map) to
  `build/rn_paras.txt` to read the actual text.
- [ ] For each of the ~11 chapters, choose a **verbatim** opening phrase as its `anchor` (grep to
  confirm it's an exact, unique-at-that-point substring). Write the JSON `[{title,anchor}…]`.
- [ ] **Verify:** `resection` produces ~11 sensible chapters with balanced word counts
  (target 8–10 min ≈ 1.2k–1.6k words; none > 18 min); titles read well.
- [ ] **Commit:** `data: Rerum Novarum chapter map (educator's thematic breakdown)`.

## Task 3 — Voice + audio generation (single British voice)

**Files:** `pipeline/voices.yaml`; audio under `docs/audio/rerum-novarum/`.

- [ ] Check disk headroom (`df -h .`); confirm room for ~12 MP3s.
- [ ] Add British voice option(s) to `voices.yaml` (e.g. `george: {ref: bm_george, label:
  "George — British narrator"}`); `audition build/rerum-novarum.html --voices
  bm_george,bm_lewis,bm_daniel` and **pick by ear**.
- [ ] Tune the `lexicon` for any proper nouns / Latin the voice fumbles (audition again).
- [ ] **Generate** (resumable, slice-first smoke test):
  `audiobook generate build/rerum-novarum.html --id rerum-novarum --title "Rerum Novarum"
  --subtitle "On Capital and Labor" --author "Pope Leo XIII" --date "1891"
  --source-url <vatican-url> --chapter-map data/chapter_maps/rerum-novarum.json --voices <pick>
  --chapters 1:1` → then full run.
- [ ] **Commit** audio: `feat(audio): Rerum Novarum, <voice> narration`.

## Task 4 — Audio QA (zoomed-in quality)

- [ ] `rm -f build/qa-report.json` then `audiobook qa --id rerum-novarum
  --source build/rerum-novarum.html --chapter-map data/chapter_maps/rerum-novarum.json`.
- [ ] Must print **QA PASSED** (WER ≤ 0.12, ~−16 LUFS, peak ≤ 0, no >3s silence, duration band).
  Debug per [qa-audit.md](../../playbook/qa-audit.md#audio); re-render offending chapters.
- [ ] **Spot-listen** ch1 + a mid chapter on the deployed voice — pleasant, clear, correct Latin/names.

## Task 5 — Companion authoring (holistic, source-honoring)

**Files:** create `pipeline/build_guide_rerum.py` (copy of `build_guide_magnifica.py`).

- [ ] Author **CONCEPTS** (the ideas RN *originates* and Magnifica extends — rich cross-links):
  the social question; **private property as a natural right**; **use vs. ownership / the universal
  destination of goods**; **the family before the State** (subsidiarity's seed); **capital & labor
  need each other**; **the dignity of work**; **the just/living wage**; **the State's duty to
  protect the weak** (preferential-concern seed); **the right of association** (the guild echo);
  **distributive justice & the common good**; **charity as the bond**. Anchors verbatim.
- [ ] **GLOSSARY** (natural law, distributive vs. commutative justice, subsidiarity-in-seed,
  the just wage, mutualism/associations) — accurate one-liners.
- [ ] **FURTHER_READING** — verified links; **cross-link to Magnifica** (and forward to Laudato si').
- [ ] **COMMENTARY** — same Asimov/Pratchett/Stephenson/ancients register; the resonance to lean on:
  an AI annotating the **founding charter of Catholic Social Teaching**, written in the first
  machine age (the loom, the factory) and now read in the second (the model, the data center).
  Reverent, clearly-labelled opinion, succinct.
- [ ] Set `has_guide:true` + `hidden:true` on the RN manifest entry from the build script.
- [ ] Build: `python -m pipeline.build_guide_rerum`; integrity:
  `python scripts/validate_guide.py rerum-novarum build/rerum-novarum.html` →
  `nonverbatim=NONE dead=NONE unique_titles=True`.
- [ ] **Commit:** `feat: Rerum Novarum companion (grounded concepts, glossary, commentary)`.

## Task 6 — Hide-behind-Shift on the library index

**Files:** `docs/index.html`, `docs/style.css`; new `docs/tests/test_index_wip.mjs`.

- [ ] Manifest: RN carries `hidden:true`. **index.html:** render hidden books with class `wip`
  (and `aria-hidden`), kept `display:none` until the grid has `show-wip`. Add `keydown`/`keyup`
  listeners: holding **Shift** adds `show-wip` (reveal), releasing removes it. Handle blur/visibility
  to avoid a stuck-revealed state. Visible books render exactly as today.
- [ ] CSS: `.wip{display:none} .grid.show-wip .wip{display:flex}` + a small "Work in progress" badge
  on the WIP card.
- [ ] **Render-guard test** `test_index_wip.mjs` (DOM shim): with a hidden book present, default
  render shows only non-hidden cards; after dispatching a Shift `keydown`, the WIP card is revealed;
  after `keyup`, hidden again. (Refactor the index's inline script into a tiny importable
  `docs/app/index.js` so it's testable — keeps the no-blank-page discipline.)
- [ ] **Verify:** `node --test docs/tests/*.mjs` green.
- [ ] **Commit:** `feat: Shift-to-reveal work-in-progress editions on the library index`.

## Task 7 — Tests + deploy + live verification

- [ ] `pytest -q` + `node --test docs/tests/*.mjs` all green (expect new chapter-map, index-wip,
  and book-aware tests added).
- [ ] `audiobook deploy`; then **live-verify** (per [qa-audit.md](../../playbook/qa-audit.md#live-verification)):
  all RN endpoints 200 (`/player.html`, `/guide/rerum-novarum.json`, `/transcript/…`, `/text/…`),
  guide serves N concepts, render JS intact; **RN absent from the default index but revealed by
  Shift**; Magnifica still fully working; byte-range 206 on an RN MP3.

## Task 8 — Critic loop (history + mystical/theology) — THE GATE

Per [critic-panel.md](../../playbook/critic-panel.md). **Loop until HONORS.**

- [ ] `python scripts/make_review_bundle.py rerum-novarum` → `build/companion_for_review.md`.
- [ ] Dispatch (parallel `Agent`) reading the bundle **+ the chapter map** against
  `build/rerum-novarum.html`:
  - **English / economic historian** — 1891 context (Industrial Revolution, the "condition of
    England," socialism/Marx, real labor conditions); also **validates the chapter breakdown**.
  - **Educator** — clarity, teachability, the through-line.
  - **Mystical / church historian & theologian** — natural-law (Thomistic) grounding, CST lineage
    Leo XIII → Pius XI → JP II → Francis → Leo XIV, fidelity to the source's claims & register.
- [ ] Apply findings (re-ground every change verbatim; fix anchors/blurbs/commentary; adjust the
  chapter map if the historian flags a boundary), rebuild, re-validate, re-test, re-deploy.
- [ ] Re-run a confirming pass. **Repeat the loop** until **both** the history and mystical critics
  return **HONORS**. Be honest about where it started.

## Definition of done (the goal's completion test)

- [ ] All tests green (`pytest` + `node --test`); new behaviors have guard tests.
- [ ] Audio QA **PASSED**; spot-listened, pleasant & clear.
- [ ] Companion: quotes verbatim, 0 dead links, unique titles; **critic verdict HONORS** from the
  history **and** mystical/theology lenses; chapter breakdown blessed by the educator/historian.
- [ ] RN live: hidden on the index, **revealed by holding Shift**, fully playable with read-along +
  full-text + companion; cross-linked with Magnifica.
- [ ] Working tree clean, pushed. Pause ~07:30 CDT.

## Notes / lessons folded in (so it doesn't stall)

- **Verify the artifact the user sees** (run the JS, curl the live URL) — not just the JSON.
- **Edits fail silently** when `old_string` doesn't match exactly — re-Read before editing
  multi-line markup; confirm with grep after.
- **`build/` is gitignored** — tracked tooling lives in `scripts/`, the chapter map in tracked
  `data/`. The cached source HTML stays in `build/`.
- Connection can drop tool output — write results to files and Read them; keep commands small.
