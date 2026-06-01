"""Build the full-text reading JSON consumed by the static reader page (text.html).

Same source-of-truth path as the audio and the read-along (load → clean → chunk), so the
on-page text matches what's spoken. Chapters keep their titles and paragraph lines; the
reader renders them in a calm, mobile-friendly long-form layout with a chapter jump-list.
This is the "read the whole thing" companion to the listen — local, no external dependency.
"""

import json

from pipeline import config
from pipeline.source_text import clean_chapters

TEXT_DIR = config.DOCS / "text"


def build_fulltext(book_id, resource, title="", author="", subtitle="", source_url="",
                   chapter_map=None, repairs=None):
    chapters = []
    for index, ctitle, lines in clean_chapters(resource, chapter_map=chapter_map, repairs=repairs):
        # lines[0] is the spoken chapter-intro ("Title."); the rest are the body sentences.
        body = lines[1:] if len(lines) > 1 else lines
        chapters.append({"index": index, "title": ctitle, "paragraphs": body})
    data = {
        "book": book_id,
        "title": title,
        "subtitle": subtitle,
        "author": author,
        "source_url": source_url,
        "chapters": chapters,
    }
    TEXT_DIR.mkdir(parents=True, exist_ok=True)
    out = TEXT_DIR / f"{book_id}.json"
    out.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")) + "\n",
                   encoding="utf-8")
    nlines = sum(len(c["paragraphs"]) for c in chapters)
    return out, len(chapters), nlines
