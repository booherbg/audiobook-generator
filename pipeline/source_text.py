"""Single source of truth for the cleaned, chunked text of a book.

Both the read-along transcript and the companion guide derive their text from here,
by running the SAME deterministic path the audio was rendered from
(load → clean → normalize-free chunk). This guarantees the on-screen words match the
spoken words and can be reproduced from a clean checkout (no scratch-file dependency).
"""

from pipeline.chapter_map import resection
from pipeline.chunk import chunk_document
from pipeline.clean import clean_paragraph, is_boilerplate
from pipeline.load import HTMLLoader


def clean_chapters(resource, chapter_map=None, repairs=None):
    """Return [(index, title, [lines])] for a URL or file.

    `lines` are the exact segments fed to TTS for that chapter: the spoken chapter
    intro first, then each narrated sentence — so they align 1:1 with the audio.

    If `chapter_map` (a list of {"title","anchor"}) is given, the cleaned paragraph stream
    is re-sectioned by it before chunking — for sources with no usable heading structure.
    The cut happens AFTER cleaning so anchors match the same text the listener hears.

    `repairs` is an optional source-specific {bad: good} map for fixing missing-space
    export defects in the original HTML (see clean.clean_paragraph).
    """
    doc = HTMLLoader().load(resource)
    for sec in doc.sections:
        sec.paragraphs = [clean_paragraph(p, repairs) for p in sec.paragraphs if not is_boilerplate(p)]
        sec.paragraphs = [p for p in sec.paragraphs if p]
    doc.sections = [s for s in doc.sections if s.paragraphs]
    if chapter_map:
        doc = resection(doc, chapter_map)
    return [(ch.index, ch.title, list(ch.segments)) for ch in chunk_document(doc)]
