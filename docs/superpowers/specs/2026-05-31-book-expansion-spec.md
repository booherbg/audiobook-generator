# Book Expansion Spec

**Goal:** Make adding a new edition (audiobook + player + read-along + full-text + companion) a
repeatable, pull-and-go process that reliably produces a *world-class, source-honoring* result —
so the next books need no re-derivation of method.

**Status:** The system and method are proven on *Magnifica Humanitas* (live, critic-verdict
HONORS). This spec captures the contract; the operational detail lives in
[`docs/playbook/`](../../playbook/README.md).

---

## Scope

**In scope:** a reusable expansion process and its quality bar, covering every layer that made
the first edition work — generation, data contracts, read-along, full-text, companion, the critic
panel, and the QA audit.

**First targets** (from [BACKLOG.md](../../../BACKLOG.md)), the two documents *Magnifica* is built on:

1. **Rerum Novarum** — Leo XIII, 1891 — origin of Catholic Social Teaching.
2. **Laudato si'** — Francis, 2015 — integral ecology.

Each gets the full treatment and becomes part of one connected library.

**Out of scope (deferred, see BACKLOG):** voiced commentary track, woven "enriched" edition, and
any audio beyond an agreed core set (storage cap). The *text* experience — read-along, full-text,
companion, critic review — can ship with **zero new audio**.

## Architecture (unchanged — reuse, don't rebuild)

The generator is deterministic and LLM-free; Claude Code supplies the judgment (sourcing,
companion authoring, critic review). One text source of truth — `source_text.clean_chapters()` —
feeds audio, read-along, full-text, and companion quotes, so on-screen always matches spoken. The
player is static vanilla JS that knows only four JSON files
([data contracts](../../playbook/data-contracts.md)). Deploy is `gh` → GitHub Pages. No API keys,
no console script, no build step.

```
source → load·clean·chunk → normalize·TTS·assemble → QA → manifest → companion → deploy
```

## Invariants — what every edition must satisfy (the contract)

1. **Honor the original.** Quotes are extracted *verbatim* by code (anchors must be exact source
   substrings); blurbs and commentary are clearly-labelled interpretation, in the source's own
   register. Each edition links back to the authoritative original.
2. **Fidelity is reviewed, not assumed.** A critic panel (educator + humanist + domain expert)
   reads the companion *against the source* and the verdict must reach **HONORS** before ship.
   Verbatim quoting is necessary but not sufficient.
3. **Voice-independent positioning.** Deep-links and read-along use `{chapter, fraction}`, never
   absolute seconds — resolved against the selected voice at click time.
4. **Verify the artifact the user sees.** Render tests execute the JS; live checks hit the
   deployed URL; audio is actually listened to. Data-only verification does not count.
5. **Respect the storage cap.** No new MP3s beyond the agreed core set without explicit
   go-ahead.
6. **Green tests, clean tree.** `pytest` + `node --test` pass; new render paths get a guard test;
   nothing unpushed at done.

## Definition of done

The per-book gate in [qa-audit.md → Definition of done](../../playbook/qa-audit.md#definition-of-done):
audio QA passed (if in scope), companion verbatim with no dead links and **critic verdict
HONORS**, all endpoints live, read-along + full-text working, link to the original present, tests
green, tree clean, cross-linked into the library.

## How (procedure)

The step-by-step runbook is **[docs/playbook/README.md](../../playbook/README.md)**, with deep
references for [data contracts](../../playbook/data-contracts.md),
[companion authoring](../../playbook/companion-authoring.md),
[the critic panel](../../playbook/critic-panel.md), and [the QA audit](../../playbook/qa-audit.md).
This spec defines *what must be true*; the playbook defines *how to make it true*.

## Known improvements to fold in when the second book lands

These are nice-to-haves observed while shipping the first edition; do them opportunistically:

- **Multi-book player wiring.** Pages currently hard-code `?book=magnifica-humanitas` in top-bar
  links and the `BOOK` default in `app/{guide,text}.js`. With a second book, read the id from the
  manifest / URL instead.
- **`has_guide` automation.** `build_guide_<id>` could set `has_guide:true` on the manifest entry
  so it isn't reset by a later `generate` (today it's a manual flip — documented in the playbook).
- **A library landing page** that lists editions and the relationships between them (further-reading
  links become live cross-edition links once siblings exist).
