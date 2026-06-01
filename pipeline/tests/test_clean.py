from pipeline.clean import clean_paragraph, is_boilerplate


def test_clean_strips_footnote_brackets():
    assert clean_paragraph("human dignity.[12]") == "human dignity."


def test_clean_strips_superscripts():
    assert clean_paragraph("the work¹ of all") == "the work of all"


def test_clean_strips_leading_paragraph_number():
    assert clean_paragraph("23. The human person is") == "The human person is"


def test_clean_collapses_whitespace():
    assert clean_paragraph("a   b\n c") == "a b c"


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
