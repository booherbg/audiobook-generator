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
