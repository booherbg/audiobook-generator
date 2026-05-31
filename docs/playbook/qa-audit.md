# World-class QA audit

Three layers — **audio**, **companion integrity**, **site** — plus **live verification** after
deploy. The governing rule sits above all of them:

> ## Verify the artifact the user sees
> A passing data check is not a working product. We once shipped a blank companion page that
> passed every JSON check — the bug was a `ReferenceError` in the render JS that no data test
> could see. The fixes were a **render test** (execute the JS) and a **live curl** (hit the
> deployed URL). For every layer below, ask: *did I verify the thing the user actually
> experiences — the rendered page, the played audio, the live endpoint — or only the data behind
> it?*

---

## Audio

Automated gross-defect detection for spoken word (not a mastering suite). Run:

```bash
rm -f build/qa-report.json     # the report is resumable; always start clean
.venv/bin/python -m pipeline qa --id <id> --source build/<id>.html
# → build/qa-report.json, prints per-chapter rows and QA PASSED / FAILED
```

Per chapter × voice, all must hold (`pipeline/qa.py`, gated in `pipeline/__main__.py`):

| Gate | Threshold | Catches |
|------|-----------|---------|
| **WER** (faster-whisper vs. the script) | ≤ 0.12 | wrong/garbled/skipped narration |
| **Loudness** (integrated LUFS) | within 2.0 of −16 | too quiet / too hot |
| **True peak** (real sample peak, astats) | ≤ 0 dBFS | clipping |
| **Silence** (silencedetect, >3s) | none | dead air, dropouts, truncation |
| **Duration band** | 120–200 wpm for the word count | runaway length / cut-off chapters |

**Debugging failures**
- **High WER:** usually a normalization miss (numbers, Latin, abbreviations) or a bad voice
  reference. Check `pipeline/normalize.py` and the `lexicon` in `voices.yaml`; re-render that
  chapter with `generate --chapters N:N --force`.
- **Clipping (true peak > 0):** the mastering chain is one-pass `loudnorm,alimiter` in
  `pipeline/assemble.py` and the gate measures the **real sample peak**, not loudnorm's predicted
  inter-sample TP. If this trips, the chain changed — don't relax the gate; fix the chain. (We
  burned real time chasing this with band-aids; the lesson is logged in memory.)
- **Silence / short duration:** almost always a render truncated by a crash. `generate` re-renders
  any MP3 under 0.6× expected, so just re-run it.

**Then actually listen.** Spot-listen chapter 1 and one mid-chapter in the *deployed* player, both
voices. The automated gates catch gross defects; your ear catches "is this pleasant and clear?"

## Companion integrity

```bash
.venv/bin/python scripts/validate_guide.py <id> build/<id>.html
# concepts=N nonverbatim=NONE dead=NONE unique_titles=True   ← all required (exits non-zero otherwise)
```

Checks every concept `quote` is an exact substring of the cleaned source, every `related`
cross-link resolves to a real card, and titles are unique. Exits non-zero on any failure, so the
checklist and any CI can gate on it.

This is necessary but not sufficient for fidelity — the **[critic panel](critic-panel.md)** is the
other half, and its verdict must be **HONORS**.

## Site

```bash
.venv/bin/python -m pytest -q          # pipeline logic (deterministic units)
node --test docs/tests/*.mjs           # player logic + render guards
```

**Render guards are mandatory for any page with a render path.** `docs/tests/test_guide_render.mjs`
and `test_text_render.mjs` execute the real `app/*.js` against the real JSON under a minimal DOM
shim and assert the page actually populated (and that the error fallback did *not* fire). This is
the test class that would have caught the blank-companion bug. If you add a page, add its guard —
copy `test_text_render.mjs` and adjust the ids/assertions.

`docs/tests/test_logic.mjs` covers the pure functions (read-along line search, fraction→seconds,
deep-link resolution). Keep player logic in `docs/app/logic.js` so it stays unit-testable.

**Manual, on a real device:** seek / lock / speed / voice-switch; read-along highlight tracks and
tap-to-seek works; full-text renders and the "read the original" link is present; layout holds on
mobile (the player is the primary surface and is used on phones).

## Live verification

After `deploy`, confirm the **live** site — Pages can lag, and a local pass doesn't prove the
deploy. Wait for propagation, then check endpoints, served data, and that render JS is intact:

```bash
.venv/bin/python - <<'PY'
import json, urllib.request
b = "https://booherbg.github.io/audiobook-generator"
pages = ["/", "/player.html", "/guide.html", "/text.html", "/about.html", "/manifest.json",
         "/guide/<id>.json", "/transcript/<id>.json", "/text/<id>.json",
         "/app/guide.js", "/app/player.js", "/app/text.js"]
codes = {p: urllib.request.urlopen(b+p).status for p in pages}
g = json.load(urllib.request.urlopen(b+"/guide/<id>.json"))
js = urllib.request.urlopen(b+"/app/guide.js").read().decode()
print("all 200:", all(c == 200 for c in codes.values()), codes)
print("concepts served:", len(g["concepts"]), "| render JS intact (slug):", "function slug" in js)
PY
```

Also confirm a byte-range request returns **206** (seeking depends on it):
`curl -sI -H "Range: bytes=0-1023" "<…>/audio/<id>/af_heart/chapter-01.mp3" | head -1`.

> A specific trap we hit: an `Edit` to add a nav link **failed silently** (the markup had wrapped
> to two lines so the match missed), and the link shipped missing. The *live* check
> (`player → Text link: False`) caught it. Trust the live check over your memory of the edit.

---

## Definition of done

A book is done when all of these hold. (See also [docs/CHECKLIST.md](../CHECKLIST.md).)

**Audio** *(only if audio is in scope this round — see the storage cap)*
- [ ] `pipeline qa --id <id>` prints **QA PASSED** (WER ≤ 0.12, ~−16 LUFS, peak ≤ 0, no >3s silence, duration in band)
- [ ] spot-listened ch1 + a mid chapter in the **deployed** player, both voices — pleasant and clear
- [ ] seek / lock / speed / voice-switch work on mobile + desktop; range requests return 206

**Companion** *(if `has_guide`)*
- [ ] `validate_guide.py` → `nonverbatim=NONE dead=NONE`, unique titles
- [ ] deep-links land in the right chapter on **both** voices; cross-links resolve
- [ ] director's-commentary clearly labelled as AI opinion
- [ ] **critic panel run (educator + humanist + domain-expert) → verdict HONORS**

**Site**
- [ ] all endpoints 200 (player / guide / text / manifest / transcript / app JS)
- [ ] read-along highlight tracks; tap-to-seek works; full-text renders; link to the original present
- [ ] `pytest` + `node --test` green; new pages have a render-guard test

**Live**
- [ ] verified on the deployed URL (not just locally); concept count + render JS confirmed live
- [ ] working tree clean, nothing unpushed

**Library**
- [ ] cross-linked with sibling editions (further-reading → live links); `BACKLOG.md` updated
