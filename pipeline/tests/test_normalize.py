from pipeline.normalize import normalize, roman_to_int


def test_roman_to_int():
    assert roman_to_int("XIV") == 14
    assert roman_to_int("IX") == 9
    assert roman_to_int("XXIII") == 23


def test_regnal_name_to_ordinal():
    assert normalize("Pope Leo XIV wrote") == "Pope Leo the Fourteenth wrote"
    assert normalize("under Leo XIII") == "under Leo the Thirteenth"


def test_chapter_roman_to_cardinal():
    assert normalize("Chapter IV begins") == "Chapter Four begins"


def test_abbreviations():
    assert normalize("cf. the text") == "see the text"
    assert normalize("e.g. this") == "for example this"
    assert normalize("i.e. that") == "that is that"


def test_smart_quotes_and_dash():
    assert normalize("“work”—often") == '"work", often'


def test_lexicon_substitution():
    assert normalize("Rerum Novarum today", {"Rerum Novarum": "Reh-rum No-vah-rum"}) == (
        "Reh-rum No-vah-rum today"
    )
