"""Build the Tier-3 companion 'study guide' JSON, grounded in the source text.

No-hallucination guarantee: every concept card's `quote` is EXTRACTED VERBATIM by this
code from the source (via pipeline.source_text — the SAME load→clean→chunk path the audio
was rendered from). The human-authored fields are `title`, `blurb` (a short conceptual
explanation) and `anchor` (a phrase that must occur in the source); the quote itself is
copied byte-for-byte from the line containing the anchor, so it cannot drift from the source.

Deep-links are stored VOICE-INDEPENDENT as {chapter, fraction} — a chapter index plus a
position in [0,1) within that chapter — so the player resolves them against whichever voice
the listener selected (the voices differ in length by ~10%; an absolute second on one voice's
timeline lands in the wrong place, sometimes the wrong chapter, on the other). `timestamp` is
kept only as a human-readable label, computed on the default (first) voice's timeline.

Director's-commentary entries are clearly-labelled AI asides (opinion, not source claims).
"""

import json
from pathlib import Path

from pipeline import config
from pipeline.source_text import clean_chapters

GUIDE_DIR = config.DOCS / "guide"


def _voice_timeline(manifest_path, voice):
    """Return ({index: start_sec}, {index: duration_sec}) for a voice, from the manifest."""
    book = json.loads(Path(manifest_path).read_text())["books"][0]
    starts, durs, t = {}, {}, 0.0
    for c in book["chapters"]:
        d = c["duration"].get(voice, 0)
        starts[c["index"]], durs[c["index"]] = t, d
        t += d
    return starts, durs


def _default_voice(manifest_path):
    book = json.loads(Path(manifest_path).read_text())["books"][0]
    return book["voices"][0]["id"] if book.get("voices") else "female"


def find_quote(chapters, anchor):
    """Find the first line containing `anchor` (case-insensitive). Returns
    (chapter_index, chapter_title, line, word_offset, chapter_total_words) or None.
    The line is returned exactly as it appears in the source."""
    low = anchor.lower()
    for idx, title, lines in chapters:
        total = sum(len(s.split()) for s in lines) or 1
        words_before = 0
        for s in lines:
            if low in s.lower():
                return idx, title, s, words_before, total
            words_before += len(s.split())
    return None


def build_guide(book_id, resource, concepts, glossary, further_reading, commentary,
                manifest_path=None):
    manifest_path = manifest_path or config.MANIFEST
    chapters = clean_chapters(resource)
    titles = {idx: title for idx, title, _ in chapters}
    voice = _default_voice(manifest_path)
    starts, durs = _voice_timeline(manifest_path, voice)

    def label_seconds(chapter, fraction):
        """Human-readable timestamp on the default voice (display only)."""
        return round(starts.get(chapter, 0) + fraction * durs.get(chapter, 0), 1)

    cards, missing = [], []
    for c in concepts:
        hit = find_quote(chapters, c["anchor"])
        if not hit:
            missing.append(c["anchor"])
            continue
        idx, title, sentence, woff, total = hit
        fraction = round(woff / total, 5)
        cards.append({
            "title": c["title"],
            "blurb": c["blurb"],
            "quote": sentence,            # verbatim, extracted from source
            "chapter": idx,
            "chapter_title": title,
            "fraction": fraction,         # voice-independent position within the chapter
            "timestamp": label_seconds(idx, fraction),  # display label (default voice)
            "related": c.get("related", []),
        })

    # Commentary is authored as absolute seconds on the default-voice timeline; convert each
    # to {chapter, fraction} so the link survives a voice switch.
    com_out = []
    for c in commentary:
        ts = c["timestamp"]
        chapter, fraction = chapters[0][0], 0.0
        placed = False
        for idx in starts:
            d = durs[idx] or 1
            if starts[idx] <= ts < starts[idx] + d:
                chapter, fraction, placed = idx, round((ts - starts[idx]) / d, 5), True
                break
        if not placed:
            chapter = max(starts, default=chapter)  # past the end → last chapter
            fraction = 0.0
        com_out.append({
            "label": c["label"],
            "text": c["text"],
            "chapter": chapter,
            "chapter_title": titles.get(chapter, ""),
            "fraction": fraction,
            "timestamp": label_seconds(chapter, fraction),
        })

    data = {
        "book": book_id,
        "intro": (
            "A companion to the reading — not a replacement for it. This encyclical asks "
            "whether our tools can serve human dignity rather than crowd it out, so there is "
            "a quiet irony in an AI keeping notes in its margins. The honest answer is "
            "restraint: everything below points back to the text in the author's own words, "
            "each quotation is verbatim, and every opinion is labelled as mine, not his. "
            "Follow a thread if you're curious; close the tab and just listen if you're not. "
            "Either is a good way to spend the hours."
        ),
        "concepts": cards,
        "glossary": glossary,
        "further_reading": further_reading,
        "commentary": com_out,
    }
    GUIDE_DIR.mkdir(parents=True, exist_ok=True)
    out = GUIDE_DIR / f"{book_id}.json"
    out.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return out, cards, missing
