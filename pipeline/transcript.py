"""Build the read-along transcript JSON consumed by the player.

For each chapter we store the exact spoken lines plus the cumulative fraction of the chapter
elapsed at the start of each line. The player multiplies that fraction by the chapter's
measured duration (per voice, from the manifest) to estimate each line's start time — enough
to highlight the current line and seek when a line is tapped, with no forced-alignment
dependency.

Timing model: a line's spoken time ≈ proportional to its characters PLUS a fixed gap — the
pipeline renders each line as its own clip joined with ~400ms of silence (assemble.PARA_PAUSE_MS)
and TTS lengthens sentence endings. Modelling that gap as PAUSE_CHARS character-equivalents keeps
short lines (e.g. scripture refs) from being under-weighted, the main source of drift in a pure
char-proportional model — it cuts modelled within-chapter highlight drift ~4× (avg ~5s → ~1s).
"""

import json
from pathlib import Path

from pipeline import config
from pipeline.source_text import clean_chapters

TRANSCRIPT_DIR = config.DOCS / "transcript"

# Char-equivalent of the inter-line gap. ~155 wpm ≈ 15.7 chars/s, so a 400ms pause ≈ 6 chars;
# add a little for sentence-final lengthening.
PAUSE_CHARS = round(config.PARA_PAUSE_MS / 1000 * (config.WPM * 6.1 / 60)) + 4


def build_transcript(book_id, resource):
    chapters = []
    for index, title, lines in clean_chapters(resource):
        # per-line weight ≈ spoken chars + the fixed rendered inter-line gap
        lengths = [len(ln) + PAUSE_CHARS for ln in lines]
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
