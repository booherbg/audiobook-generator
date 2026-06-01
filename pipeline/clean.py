"""Clean extracted text for narration: drop footnote markers, paragraph numbers,
and boilerplate lines. Operates on plain paragraph strings.
"""

import re

_FOOTNOTE_BRACKET = re.compile(r"\[\d+\]")
# Inline citation markers as parenthesised numbers, e.g. "…working classes.(1) It is…" or
# "obstacles;(9) that…". Common in older Vatican texts (Rerum Novarum). Strip the marker but
# keep surrounding text/punctuation, so it isn't narrated as a stray number.
_FOOTNOTE_PAREN = re.compile(r"\(\d{1,3}\)")
_SUPERSCRIPT = re.compile(r"[¹²³⁰-⁹]+")
_LEADING_NUM = re.compile(r"^\s*\d+\.\s+")
_WS = re.compile(r"\s+")
# Missing space after sentence/clause punctuation, e.g. "world,should" -> "world, should".
# Always safe (a letter immediately after ,;:.!? is never intended). Excludes decimals
# like "5.21" (handled only when the trailing char is a LETTER) and abbreviations are
# already expanded downstream.
_PUNCT_NOSPACE = re.compile(r"([,;:])([A-Za-z])")
# Missing space after a closing quote that ends a sentence, e.g. 'soul?"This' -> 'soul?" This'.
# Requires sentence-ending punctuation + closing quote + a capital, so it never fires mid-word.
_QUOTE_NOSPACE = re.compile(r'([.?!]["”])([A-Z])')

# End-matter footnote/reference entries, e.g. "2). Deut. 5:21." or "11). Summa theologiae…"
# — a number, a close-paren, a period, then a citation. These trail many Vatican texts and
# must never be narrated. (Distinct from in-body paragraph numbers handled by _LEADING_NUM.)
_REFERENCE_ENTRY = re.compile(r"^\s*\d+\s*\)\s*\.")

_BOILERPLATE = (
    "copyright",
    "libreria editrice vaticana",
    "dicastero",
    "all rights reserved",
    "table of contents",
    "back to top",
)


def is_boilerplate(line: str) -> bool:
    """True for empty lines or known non-content boilerplate (incl. end-matter references)."""
    low = line.strip().lower()
    if not low:
        return True
    if low == "references:" or _REFERENCE_ENTRY.match(low):
        return True
    return any(token in low for token in _BOILERPLATE)


def clean_paragraph(text: str, repairs: dict | None = None) -> str:
    """Strip footnote markers, a leading paragraph number, and excess whitespace.

    `repairs` is an optional source-specific map of glued/garbled tokens to their correct
    form (e.g. {"ofrevolutionary": "of revolutionary"}) for fixing missing-space export
    defects in the original HTML. Applied as whole-word substitutions; curated per source
    (a heuristic splitter mangles real words like "workers"→"work ers", so we don't guess).
    """
    text = _FOOTNOTE_BRACKET.sub("", text)
    text = _FOOTNOTE_PAREN.sub("", text)
    text = _SUPERSCRIPT.sub("", text)
    text = _LEADING_NUM.sub("", text)
    text = _PUNCT_NOSPACE.sub(r"\1 \2", text)
    text = _QUOTE_NOSPACE.sub(r"\1 \2", text)
    if repairs:
        for bad, good in repairs.items():
            # Anchor with \b only on the sides that start/end with a word char — a key like
            # "Apostle with," ends in punctuation, where a trailing \b can never match.
            lead = r"\b" if bad[:1].isalnum() else ""
            trail = r"\b" if bad[-1:].isalnum() else ""
            text = re.sub(rf"{lead}{re.escape(bad)}{trail}", good, text)
    return _WS.sub(" ", text).strip()
