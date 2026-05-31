# Manual QA Checklist

Run on the live site across browsers. Mark ✓ / ✗.

| Check | Chrome | Firefox | Safari | iOS Safari | Android Chrome |
|---|---|---|---|---|---|
| Library loads (cover, title, author, duration) | | | | | |
| Open book → player loads from `?book=` | | | | | |
| Play / pause (button + tap) | | | | | |
| Scrubber seek (drag to position) | | | | | |
| Skip back 15s / forward 30s | | | | | |
| Next / previous chapter | | | | | |
| Speed 0.75×–2× applies and persists on reload | | | | | |
| Voice switch keeps chapter + position | | | | | |
| Chapter list: jump, current highlighted, completed ✓ | | | | | |
| Resume last position after reload | | | | | |
| Lock-screen / notification / media-key controls (Media Session) | | | | | |
| Artwork shows on lock screen | | | | | |
| Responsive, usable one-handed on phone | | | | | |
| Keyboard: Space, ← →, `[` `]` | ✓ | ✓ | ✓ | n/a | n/a |
| Range-request seeking works (jump far ahead loads fast) | | | | | |

**Audio spot-check (by ear):** play ≥2 full chapters per voice — clear, pleasant, correct
pronunciation of names/Latin (e.g. *Rerum Novarum*, "AI"); no clipping, dropouts, or long gaps.

Notes:
- 2026-05-30: Tier 1 shipped. Automated verification PASS: audio QA 34/34 (both voices,
  WER avg ~1.7% / max ~7%, sample peak <0 on every file, loudness ~-16.7 to -17.7 LUFS,
  no >3s silence gaps, durations in band). pytest 30 passed, node:test 7/7. Live endpoints
  all 200 (index, manifest, player, app/logic.js) + 200 byte-range on both voices' MP3s.
  Live manifest confirmed: 2 voices, 17 chapters.
- Manual cross-browser/device matrix below: pending hands-on pass by a human (the player uses
  standard HTMLAudioElement + Media Session; desktop keyboard row verified in code/logic tests).
