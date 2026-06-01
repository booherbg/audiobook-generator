from pipeline.clean import clean_paragraph, is_boilerplate


def test_clean_strips_footnote_brackets():
    assert clean_paragraph("human dignity.[12]") == "human dignity."


def test_clean_strips_inline_paren_footnote_markers():
    # Older Vatican texts mark citations as parenthesised numbers inline; never narrate them.
    assert clean_paragraph("the working classes.(1) It is a subject") == "the working classes. It is a subject"
    assert clean_paragraph("obstacles;(9) that the rich") == "obstacles; that the rich"


def test_clean_strips_superscripts():
    assert clean_paragraph("the work¹ of all") == "the work of all"


def test_clean_strips_leading_paragraph_number():
    assert clean_paragraph("23. The human person is") == "The human person is"


def test_clean_collapses_whitespace():
    assert clean_paragraph("a   b\n c") == "a b c"


def test_clean_adds_space_after_punctuation():
    # MS-Word exports drop spaces after clause punctuation, e.g. "world,should".
    assert clean_paragraph("the world,should have") == "the world, should have"
    assert clean_paragraph("first;second") == "first; second"
    # but NOT inside a decimal/number where the next char is a digit
    assert clean_paragraph("chapter 5:21 of") == "chapter 5:21 of"


def test_clean_applies_source_repairs():
    # Curated per-source repair map fixes glued words a heuristic can't safely split.
    repairs = {"ofrevolutionary": "of revolutionary", "inthe": "in the"}
    assert clean_paragraph("the spirit ofrevolutionary change", repairs) == "the spirit of revolutionary change"
    assert clean_paragraph("felt inthe sphere", repairs) == "felt in the sphere"
    # a word NOT in the map is left untouched (no heuristic guessing)
    assert clean_paragraph("the workers labored", repairs) == "the workers labored"


def test_clean_adds_space_after_closing_quote():
    # Missing space after a sentence-ending closing quote, e.g. 'soul?"This' -> 'soul?" This'.
    assert clean_paragraph('his soul?"This, as our Lord') == 'his soul?" This, as our Lord'
    assert clean_paragraph('unto you."Let our') == 'unto you." Let our'
    # must not touch a quote that isn't sentence-final or isn't followed by a capital
    assert clean_paragraph('the "good" man') == 'the "good" man'


def test_clean_repair_key_ending_in_punctuation():
    # A repair key ending in punctuation (e.g. "Apostle with,") must still match — the
    # word-boundary anchor is applied only on sides that start/end with a word char.
    repairs = {"Apostle with,": "Apostle saith,"}
    assert clean_paragraph("Whence the Apostle with, Command", repairs) == "Whence the Apostle saith, Command"
    # a word-bounded key must NOT match inside a longer word
    assert clean_paragraph("reworked the work", {"work": "WORK"}) == "reworked the WORK"


def test_is_boilerplate():
    assert is_boilerplate("Copyright © Dicastero per la Comunicazione")
    assert is_boilerplate("   ")
    assert not is_boilerplate("The dignity of work")


def test_is_boilerplate_drops_end_matter_references():
    # End-matter footnote/reference entries (e.g. Rerum Novarum's reference list) must
    # never be narrated. They look like "2). Deut. 5:21." or "11). Summa theologiae…".
    assert is_boilerplate("REFERENCES:")
    assert is_boilerplate("2). Deut. 5:21.")
    assert is_boilerplate("11). Summa theologiae , IIa-IIae, q. lxvi, art. 2, Answer.")
    # A real body paragraph that merely starts with a number must survive (it's not a
    # reference entry — no ")." after the digits; clean_paragraph handles the bare number).
    assert not is_boilerplate("23. The human person is an end, not a means.")
