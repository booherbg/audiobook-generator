"""Normalize text into something a TTS engine narrates well: expand regnal/
chapter numerals, common abbreviations, and typographic punctuation, and apply
an optional pronunciation lexicon.
"""

import re

_VALS = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100, "D": 500, "M": 1000}

_ORDINALS = [
    "zeroth", "first", "second", "third", "fourth", "fifth", "sixth", "seventh",
    "eighth", "ninth", "tenth", "eleventh", "twelfth", "thirteenth", "fourteenth",
    "fifteenth", "sixteenth", "seventeenth", "eighteenth", "nineteenth", "twentieth",
    "twenty-first", "twenty-second", "twenty-third", "twenty-fourth",
]
_CARDINALS = [
    "zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine",
    "ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen", "sixteen",
    "seventeen", "eighteen", "nineteen", "twenty",
]

# Regnal first-names that take an ordinal ("Leo XIV" -> "Leo the Fourteenth").
# "John Paul" precedes "John" so the longer name matches first.
_REGNAL = (
    "John Paul|Leo|John|Paul|Pius|Benedict|Francis|Gregory|Innocent|Clement|"
    "Urban|Boniface|Alexander|Julius|Sixtus|Adrian|Celestine|Honorius"
)
# Case-insensitive so an all-caps masthead ("POPE LEO XIII") expands too; the name is
# matched without regard to case (the numeral is uppercase Roman either way).
_REGNAL_RE = re.compile(rf"\b({_REGNAL}) ([IVXLCDM]+)\b", re.IGNORECASE)
_DIVISION_RE = re.compile(r"\b(Chapter|Part|Book|Section) ([IVXLCDM]+)\b", re.IGNORECASE)

_ABBREV = [
    (re.compile(r"\bcf\.", re.IGNORECASE), "see"),
    (re.compile(r"\be\.g\.", re.IGNORECASE), "for example"),
    (re.compile(r"\bi\.e\.", re.IGNORECASE), "that is"),
    (re.compile(r"\bSts\.\s"), "Saints "),
    (re.compile(r"\bSt\.\s"), "Saint "),
    (re.compile(r"\bno\.\s"), "number "),
    (re.compile(r"\bvs\.", re.IGNORECASE), "versus"),
]

_WS = re.compile(r"\s+")


def roman_to_int(s: str) -> int:
    total, prev = 0, 0
    for ch in reversed(s.upper()):
        v = _VALS[ch]
        total += -v if v < prev else v
        prev = max(prev, v)
    return total


def _ord_word(n: int) -> str:
    return _ORDINALS[n].capitalize() if n < len(_ORDINALS) else str(n)


def _card_word(n: int) -> str:
    return _CARDINALS[n].capitalize() if n < len(_CARDINALS) else str(n)


def normalize_punct(text: str) -> str:
    text = text.replace("’", "'").replace("‘", "'")
    text = text.replace("“", '"').replace("”", '"')
    text = text.replace("—", ", ").replace("–", ", ")
    text = text.replace("…", "...")
    return text


def normalize(text: str, lexicon: dict | None = None) -> str:
    if lexicon:
        for term, repl in lexicon.items():
            text = re.sub(rf"\b{re.escape(term)}\b", repl, text)
    text = _DIVISION_RE.sub(
        lambda m: f"{m.group(1)} {_card_word(roman_to_int(m.group(2)))}", text
    )
    text = _REGNAL_RE.sub(
        lambda m: f"{m.group(1)} the {_ord_word(roman_to_int(m.group(2)))}", text
    )
    for rx, repl in _ABBREV:
        text = rx.sub(repl, text)
    text = normalize_punct(text)
    return _WS.sub(" ", text).strip()
