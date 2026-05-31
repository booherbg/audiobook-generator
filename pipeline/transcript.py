"""Build the read-along transcript JSON consumed by the player.

For each chapter we store the exact spoken lines (intro + sentences) plus the cumulative
character fraction at the start of each line. The player multiplies that fraction by the
chapter's measured duration (per voice, from the manifest) to estimate each line's start
time — good enough to highlight the current line and to seek when a line is tapped, with
no forced-alignment dependency. Char-proportional tracks TTS pacing well because longer
text (and its punctuation pauses) takes proportionally longer to speak.
"""

import json
from pathlib import Path

from pipeline import config
from pipeline.source_text import clean_chapters

TRANSCRIPT_DIR = config.DOCS / "transcript"


def build_transcript(book_id, resource):
    chapters = []
    for index, title, lines in clean_chapters(resource):
        # cumulative character offset at the start of each line (spaces count as 1)
        lengths = [len(ln) + 1 for ln in lines]  # +1 ≈ inter-line gap
        total = sum(lengths) or 1
        cum, acc = [], 0
        for L in lengths:
            cum.append(round(acc / total, 5))
            acc += L
        chapters.append({
            "index": index,
            "title": title,
            "lines": lines,
            "starts": cum,   # fraction [0,1) of chapter elapsed at each line's start
        })
    data = {"book": book_id, "chapters": chapters}
    TRANSCRIPT_DIR.mkdir(parents=True, exist_ok=True)
    out = TRANSCRIPT_DIR / f"{book_id}.json"
    out.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")) + "\n",
                   encoding="utf-8")
    nlines = sum(len(c["lines"]) for c in chapters)
    return out, len(chapters), nlines
