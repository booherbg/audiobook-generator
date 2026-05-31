"""Single source of truth for the cleaned, chunked text of a book.

Both the read-along transcript and the companion guide derive their text from here,
by running the SAME deterministic path the audio was rendered from
(load → clean → normalize-free chunk). This guarantees the on-screen words match the
spoken words and can be reproduced from a clean checkout (no scratch-file dependency).
"""

from pipeline.chunk import chunk_document
from pipeline.clean import clean_paragraph, is_boilerplate
from pipeline.load import HTMLLoader


def clean_chapters(resource):
    """Return [(index, title, [lines])] for a URL or file.

    `lines` are the exact segments fed to TTS for that chapter: the spoken chapter
    intro first, then each narrated sentence — so they align 1:1 with the audio.
    """
    doc = HTMLLoader().load(resource)
    for sec in doc.sections:
        sec.paragraphs = [clean_paragraph(p) for p in sec.paragraphs if not is_boilerplate(p)]
        sec.paragraphs = [p for p in sec.paragraphs if p]
    doc.sections = [s for s in doc.sections if s.paragraphs]
    return [(ch.index, ch.title, list(ch.segments)) for ch in chunk_document(doc)]
