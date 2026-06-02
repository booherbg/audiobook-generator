# Critic panel — the nerd review

A companion can pass every automated check — quotes verbatim, no dead links, page renders — and
still quietly betray the source by flattening or secularizing its claims. Automated checks can't
catch that. **A panel of domain-expert readers can.**

This is the step that took the *Magnifica* companion from **MOSTLY-HONORS** to **HONORS**. Run it
for every book. It is not a rubber stamp.

## How it works

1. **Regenerate a flat review bundle** from the *built* guide JSON (so critics read exactly what
   ships, not your intentions):
   ```bash
   .venv/bin/python scripts/make_review_bundle.py <id>   # writes build/companion_for_review.md
   ```
   (This just flattens `docs/guide/<id>.json` into readable markdown — see the bottom of this file
   for what it does.)

2. **Dispatch three subagents in parallel** (`general-purpose`), each a different lens,
   each reading the bundle **against the cleaned source** (`data/sources/<id>.html`).
   Three lenses that worked well:
   - **Educator** — is it clear, accurate, and genuinely helpful to a curious non-expert? Does it
     teach, or just decorate?
   - **Humanist** — does it engage the ideas honestly and humanely, without dogmatism or
     evangelism? Right register for the intended reader?
   - **Domain expert** — for these encyclicals, a scholar of the relevant tradition (Catholic
     intellectual / Catholic Social Teaching / patristics & the mystical tradition). **Does it
     honor the source's actual claims, in the source's own register?** This lens catches
     secularization and flattening.

   Pick the third lens to fit the book (a sci-fi novel might want a literature scholar + a
   historian of science + an ethicist). Always include one expert in the source's own tradition.

3. **Each returns:** per-finding severity, exact source-line citations, and a verdict —
   **HONORS / MOSTLY-HONORS-WITH-FIXES / DISTORTS.**

4. **Apply the findings**, re-grounding every change in verbatim source text (fix anchors, deepen
   blurbs, add missing concepts, correct the commentary). Rebuild
   (`uv run audiobook regenerate <id> --skip-audio`), re-validate
   (`scripts/validate_guide.py <id> data/sources/<id>.html`).

5. **Re-run one confirming audit** (the domain expert is usually enough) to verify the fixes
   landed and the verdict is now **HONORS.** Apply only quick wins from the second pass.

**Done = HONORS.** Be honest in your summary about where it started (e.g. "it was MOSTLY-HONORS
before the pass") — that honesty is part of honoring the work.

## The rubric

| Verdict | Meaning | Action |
|---------|---------|--------|
| **HONORS** | Faithful to the source's claims and register; quotes verbatim; interpretation clearly marked and accurate. | Ship. |
| **MOSTLY-HONORS-WITH-FIXES** | Sound overall but some blurbs flatten/secularize, an anchor is weak, or a key idea is missing. | Apply fixes, rebuild, re-audit to HONORS. |
| **DISTORTS** | Misrepresents what the source claims, or invents emphasis the source doesn't have. | Stop. Re-author from the source. |

## Ready-to-paste prompts

Fill in `<id>`, `<TITLE>`, `<AUTHOR>`, the source description, and the third lens. Dispatch all
three at once (parallel subagent calls, one per lens), then a single confirming run after fixes.

> **Shared preamble** (prepend to each):
> *You are reviewing an AI-built "companion" to <AUTHOR>'s <TITLE> (<one-line description>).
> Read BOTH the companion and the source, then judge fidelity. The companion's concept QUOTES are
> extracted verbatim from the source by code; your job is to judge the **blurbs, commentary,
> glossary, selection, and emphasis** — does the companion honor what the source actually claims,
> in its own register? Companion: `build/companion_for_review.md`. Source (chapter-marked):
> `data/sources/<id>.html`. Cite source line numbers. Do not rubber-stamp.*

**Educator lens (append):**
> *Lens: a gifted teacher introducing this to a curious, technical, non-specialist reader. Is each
> card clear and accurate? Does it teach the idea or just gesture at it? Is anything misleading,
> oversimplified, or jargon-y without payoff? Is the through-line followable? End with per-finding
> severity, then a verdict: HONORS / MOSTLY-HONORS-WITH-FIXES / DISTORTS, with one-line fixes.*

**Humanist lens (append):**
> *Lens: a thoughtful humanist reader. Does the companion engage the ideas honestly and humanely,
> without dogmatism or evangelism, suited to a reader who is open but not committed? Does it
> respect the reader's intelligence and the author's seriousness? Flag anything preachy,
> dismissive, or tonally off. **The commentary asides are a named character — Andrew (see the
> persona charter in `companion-authoring.md`): are they recognizably his (dry, specific, the
> insight and the flavor in one sentence) and never generic "AI commentary" (no "as an AI," no
> uplift bow)? Does each stay clearly labelled opinion, never laid over the text — and never claim
> to be human, speak for the author, or assert as fact what the source doesn't say?** End with
> per-finding severity, then a verdict, with one-line fixes.*

**Domain-expert lens (append — example for a Catholic encyclical):**
> *Lens: a scholar of the Catholic intellectual and spiritual tradition (patristics, scholasticism,
> Catholic Social Teaching, the mystical tradition). Does the companion ground each idea where the
> source grounds it (e.g. dignity as ontological — "willed, created and loved by God" — not merely
> anti-productivity)? Is any theology secularized or flattened? Is a load-bearing idea missing, or
> anchored to a heading instead of the claim? Verify new quotes are verbatim and correctly framed.
> Cite source lines. End with per-finding severity, then a verdict, with one-line fixes.*

**Anti-drivel / voice lens (append) — THE GATE for the commentary asides.** Run this on the asides
specifically, as a cook-until-clean loop (draft → critique → fix → re-critique); the set passes only
when every aside is CLEAN. The human ear signs off last — this lens will rubber-stamp euphonious slop
that a person catches (failure-mode K).
> *Lens: a ruthless anti-AI-drivel critic. The asides are the one surface that can undermine the
> project — a glib line poisons trust in the exact tooling around it. Judge HARD; default to flagging.
> Read the shipped Magnifica/Rerum asides (`pipeline/build_guide_magnifica.py`,
> `pipeline/build_guide_rerum.py`) as the bar: each aside RESISTS the facile reading and earns a
> harder one; its wit is EARNED BY ERUDITION (a real reference from inside the text's lineage), never
> a quip; it is reverent to the text and humanizes the maker; it STANDS ALONE; one idea; the last
> sentence DEEPENS, never mic-drops. Hunt these failure modes, quoting the exact phrase: (A) glib
> quip / wit not earned by understanding; (B) cheap substitution gimmick ("swap X for Y and the
> sentence barely changes"); (C) tidy-bow / mic-drop ending; (D) broken/strained metaphor; (E)
> performance-tell ("read it slowly," "notice the grammar"); (F) slogan-shaped clause that chimes
> instead of argues; (G) the "not X but Y" antithesis cadence used more than once across the set —
> flag ONLY when ornamental (an earned contrast carrying the source's actual distinction is fine);
> (H) repeated formula opener; (I) restatement of the concept or of another aside; (J) AI tells
> (uplift, "as an AI," manufactured rapport, both-sidesing); (K) bare AI-self-reference or performed
> humility that scans as modest but earns nothing. Per aside: CLEAN / DRIVEL-RISK + the failure
> letters + exact phrases + a one-line fix. SET VERDICT: PASS only if all CLEAN; else name the single
> highest-value edit. This is a gate, not a vibe check.*

**Confirming pass (after fixes):**
> *(Domain-expert preamble +) A prior panel found this MOSTLY-HONORS-WITH-FIXES; specific fixes
> were applied. For each claimed fix, confirm it actually landed and is faithful (per-item
> YES/PARTIAL/NO). Flag anything still shallow or any NEW problem the additions created. End with a
> final verdict: HONORS / MOSTLY-HONORS-WITH-FIXES / DISTORTS.*

## Review-bundle helper

`scripts/make_review_bundle.py` (shipped in the repo) flattens the built guide into readable
markdown for the critics — concept cards (blurb + verbatim quote), commentary, and glossary —
writing `build/companion_for_review.md`. Run `python scripts/make_review_bundle.py <id>`.
