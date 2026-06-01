"""Clean extracted text for narration: drop footnote markers, paragraph numbers,
and boilerplate lines. Operates on plain paragraph strings.
"""

import re

_FOOTNOTE_BRACKET = re.compile(r"\[\d+\]")
_SUPERSCRIPT = re.compile(r"[¹²³⁰-⁹]+")
_LEADING_NUM = re.compile(r"^\s*\d+\.\s+")
_WS = re.compile(r"\s+")

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


def clean_paragraph(text: str) -> str:
    """Strip footnote markers, a leading paragraph number, and excess whitespace."""
    text = _FOOTNOTE_BRACKET.sub("", text)
    text = _SUPERSCRIPT.sub("", text)
    text = _LEADING_NUM.sub("", text)
    return _WS.sub(" ", text).strip()
