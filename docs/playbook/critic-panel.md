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

2. **Dispatch three subagents in parallel** (`Agent`, `general-purpose`), each a different lens,
   each reading the bundle **against the cleaned source** (`build/<id>.html` or `build/clean.txt`).
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
   (`python -m pipeline.build_guide_<id>`), re-validate (`build/validate_guide.py`).

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
three at once (parallel `Agent` calls), then a single confirming run after fixes.

> **Shared preamble** (prepend to each):
> *You are reviewing an AI-built "companion" to <AUTHOR>'s <TITLE> (<one-line description>).
> Read BOTH the companion and the source, then judge fidelity. The companion's concept QUOTES are
> extracted verbatim from the source by code; your job is to judge the **blurbs, commentary,
> glossary, selection, and emphasis** — does the companion honor what the source actually claims,
> in its own register? Companion: `build/companion_for_review.md`. Source (chapter-marked):
> `build/<id>.html` (or `build/clean.txt`). Cite source line numbers. Do not rubber-stamp.*

**Educator lens (append):**
> *Lens: a gifted teacher introducing this to a curious, technical, non-specialist reader. Is each
> card clear and accurate? Does it teach the idea or just gesture at it? Is anything misleading,
> oversimplified, or jargon-y without payoff? Is the through-line followable? End with per-finding
> severity, then a verdict: HONORS / MOSTLY-HONORS-WITH-FIXES / DISTORTS, with one-line fixes.*

**Humanist lens (append):**
> *Lens: a thoughtful humanist reader. Does the companion engage the ideas honestly and humanely,
> without dogmatism or evangelism, suited to a reader who is open but not committed? Does it
> respect the reader's intelligence and the author's seriousness? Flag anything preachy,
> dismissive, or tonally off. End with per-finding severity, then a verdict, with one-line fixes.*

**Domain-expert lens (append — example for a Catholic encyclical):**
> *Lens: a scholar of the Catholic intellectual and spiritual tradition (patristics, scholasticism,
> Catholic Social Teaching, the mystical tradition). Does the companion ground each idea where the
> source grounds it (e.g. dignity as ontological — "willed, created and loved by God" — not merely
> anti-productivity)? Is any theology secularized or flattened? Is a load-bearing idea missing, or
> anchored to a heading instead of the claim? Verify new quotes are verbatim and correctly framed.
> Cite source lines. End with per-finding severity, then a verdict, with one-line fixes.*

**Confirming pass (after fixes):**
> *(Domain-expert preamble +) A prior panel found this MOSTLY-HONORS-WITH-FIXES; specific fixes
> were applied. For each claimed fix, confirm it actually landed and is faithful (per-item
> YES/PARTIAL/NO). Flag anything still shallow or any NEW problem the additions created. End with a
> final verdict: HONORS / MOSTLY-HONORS-WITH-FIXES / DISTORTS.*

## Review-bundle helper

`scripts/make_review_bundle.py` (shipped in the repo) flattens the built guide into readable
markdown for the critics — concept cards (blurb + verbatim quote), commentary, and glossary —
writing `build/companion_for_review.md`. Run `python scripts/make_review_bundle.py <id>`.
