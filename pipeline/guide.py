"""Build the Tier-3 companion 'study guide' JSON, grounded in the cleaned source text.

No-hallucination guarantee: every concept card's `quote` is EXTRACTED VERBATIM by this
code from build/clean.txt (the same cleaned text the audio was rendered from). The human
authored fields are `title`, `blurb` (a short conceptual explanation) and `anchor` (a
phrase that must occur in the source); the quote itself is copied byte-for-byte from the
sentence containing the anchor, so it cannot drift from the source. Chapter index and an
approximate audio timestamp are computed from the manifest.

Director's-commentary entries are clearly-labelled AI asides (opinion, not source claims).
"""

import json
import re
from pathlib import Path

from pipeline import config

CLEAN = config.BUILD / "clean.txt"
GUIDE_DIR = config.DOCS / "guide"


def _load_chapters():
    """Return [(index, title, [sentences])] from the chapter-marked clean text."""
    text = CLEAN.read_text(encoding="utf-8")
    chapters = []
    cur = None
    for line in text.splitlines():
        m = re.match(r"=====\s*CHAPTER\s+(\d+):\s*(.*?)\s*=====", line)
        if m:
            cur = (int(m.group(1)), m.group(2), [])
            chapters.append(cur)
        elif cur is not None and line.strip():
            cur[2].append(line.strip())
    return chapters


def _chapter_starts(manifest_path, voice="female"):
    """Cumulative start time (seconds) per chapter index, from the manifest durations."""
    book = json.loads(Path(manifest_path).read_text())["books"][0]
    starts, t = {}, 0.0
    for c in book["chapters"]:
        starts[c["index"]] = t
        t += c["duration"].get(voice, 0)
    return starts


def find_quote(chapters, anchor):
    """Find the first sentence containing `anchor` (case-insensitive). Returns
    (chapter_index, chapter_title, sentence, word_offset_in_chapter) or None.
    The sentence is returned exactly as it appears in the source."""
    low = anchor.lower()
    for idx, title, sents in chapters:
        words_before = 0
        for s in sents:
            if low in s.lower():
                return idx, title, s, words_before
            words_before += len(s.split())
    return None


def build_guide(book_id, concepts, glossary, further_reading, commentary, manifest_path=None):
    chapters = _load_chapters()
    starts = _chapter_starts(manifest_path or config.MANIFEST)
    wpm = config.WPM

    cards = []
    missing = []
    for c in concepts:
        hit = find_quote(chapters, c["anchor"])
        if not hit:
            missing.append(c["anchor"])
            continue
        idx, title, sentence, woff = hit
        ts = starts.get(idx, 0) + (woff / wpm * 60.0)
        cards.append({
            "title": c["title"],
            "blurb": c["blurb"],
            "quote": sentence,            # verbatim, extracted from source
            "chapter": idx,
            "chapter_title": title,
            "timestamp": round(ts, 1),
            "related": c.get("related", []),
        })

    data = {
        "book": book_id,
        "intro": (
            "An optional companion to the audiobook. Tap a concept to read a short, plain "
            "explanation, see the encyclical's own words, and jump to that moment in the "
            "audio. Everything in quotation marks is taken verbatim from the text."
        ),
        "concepts": cards,
        "glossary": glossary,
        "further_reading": further_reading,
        "commentary": commentary,
    }
    GUIDE_DIR.mkdir(parents=True, exist_ok=True)
    out = GUIDE_DIR / f"{book_id}.json"
    out.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return out, cards, missing
