"""Clean extracted text for narration: drop footnote markers, paragraph numbers,
and boilerplate lines. Operates on plain paragraph strings.
"""

import re

_FOOTNOTE_BRACKET = re.compile(r"\[\d+\]")
_SUPERSCRIPT = re.compile(r"[¹²³⁰-⁹]+")
_LEADING_NUM = re.compile(r"^\s*\d+\.\s+")
_WS = re.compile(r"\s+")

_BOILERPLATE = (
    "copyright",
    "libreria editrice vaticana",
    "dicastero",
    "all rights reserved",
    "table of contents",
    "back to top",
)


def is_boilerplate(line: str) -> bool:
    """True for empty lines or known non-content boilerplate."""
    low = line.strip().lower()
    if not low:
        return True
    return any(token in low for token in _BOILERPLATE)


def clean_paragraph(text: str) -> str:
    """Strip footnote markers, a leading paragraph number, and excess whitespace."""
    text = _FOOTNOTE_BRACKET.sub("", text)
    text = _SUPERSCRIPT.sub("", text)
    text = _LEADING_NUM.sub("", text)
    return _WS.sub(" ", text).strip()
