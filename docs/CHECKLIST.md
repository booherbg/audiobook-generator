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
