"""Re-section a Document using a curated chapter map.

Some sources (e.g. Rerum Novarum) have no usable heading structure — they load as one
long run of paragraphs. A chapter map is a small, tracked, human-authored list of
``{"title", "anchor"}`` entries: each anchor is a VERBATIM phrase marking where that
chapter begins. ``resection`` cuts the flattened paragraph stream at those anchors, so the
same deterministic boundaries feed audio, read-along, full-text, and the companion.

Anchors are matched case-insensitively and SEQUENTIALLY — each is found at or after the
previous chapter's start, so a phrase that recurs doesn't pull a later chapter backwards.
A leading run of paragraphs before the first anchor (front matter) folds into chapter one.
"""

import json
from pathlib import Path

from pipeline.model import Section


def load_map(path):
    """Load a chapter map [{"title","anchor"}, ...] from a JSON file."""
    return json.loads(Path(path).read_text(encoding="utf-8"))


def resection(doc, chapter_map):
    """Return ``doc`` with its sections replaced by the chapter map's chapters.

    Raises ValueError if an anchor cannot be found (at/after the previous anchor) — a
    loud failure so a stale map can't silently mis-chapter a book.
    """
    paras = [p for sec in doc.sections for p in sec.paragraphs]

    starts, cursor = [], 0
    for ch in chapter_map:
        needle = ch["anchor"].lower()
        i = next((k for k in range(cursor, len(paras)) if needle in paras[k].lower()), None)
        if i is None:
            raise ValueError(f"chapter-map anchor not found at/after paragraph {cursor}: "
                             f"{ch['anchor']!r}")
        starts.append(i)
        cursor = i + 1

    sections = []
    for n, (ch, start) in enumerate(zip(chapter_map, starts)):
        end = starts[n + 1] if n + 1 < len(starts) else len(paras)
        # The first chapter absorbs any front matter before its anchor.
        body = paras[:end] if n == 0 else paras[start:end]
        sections.append(Section(ch["title"], body))

    doc.sections = sections
    return doc
