"""Turn a Document into narratable Chapters: split by section heading, sub-split
overly long sections at paragraph boundaries, and prepend a spoken intro.
"""

import re

from pipeline.config import MAX_CHAPTER_MIN, WPM
from pipeline.model import Chapter, Document

_SENT_RE = re.compile(r'(?<=[.!?])["”\')\]]?\s+(?=[A-Z"“(])')


def estimate_minutes(words: int) -> float:
    return words / WPM


def split_sentences(paragraph: str) -> list[str]:
    p = paragraph.strip()
    if not p:
        return []
    return [s.strip() for s in _SENT_RE.split(p) if s.strip()]


def _pack_paragraphs(para_sents: list[list[str]], max_min: float) -> list[list[list[str]]]:
    """Greedily pack whole paragraphs into parts under the per-chapter word limit."""
    limit = max_min * WPM
    parts: list[list[list[str]]] = []
    cur: list[list[str]] = []
    cur_words = 0
    for sents in para_sents:
        w = sum(len(s.split()) for s in sents)
        if cur and cur_words + w > limit:
            parts.append(cur)
            cur, cur_words = [], 0
        cur.append(sents)
        cur_words += w
    if cur:
        parts.append(cur)
    return parts or [[]]


def chunk_document(doc: Document, max_min: float = MAX_CHAPTER_MIN) -> list[Chapter]:
    chapters: list[Chapter] = []
    idx = 0
    for sec in doc.sections:
        para_sents = [split_sentences(p) for p in sec.paragraphs if p.strip()]
        para_sents = [ps for ps in para_sents if ps]
        if not para_sents:
            continue
        for pi, part in enumerate(_pack_paragraphs(para_sents, max_min)):
            idx += 1
            if pi == 0:
                title = sec.heading
                intro = f"{sec.heading}."
            else:
                title = f"{sec.heading} (continued)"
                intro = f"{sec.heading}, continued."
            segments = [intro]
            for sents in part:
                segments.extend(sents)
            chapters.append(Chapter(index=idx, title=title, segments=segments))
    return chapters
