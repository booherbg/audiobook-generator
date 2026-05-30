from pipeline.chunk import chunk_document, estimate_minutes, split_sentences
from pipeline.model import Document, Section


def test_split_sentences():
    assert split_sentences("One thing. Two things! Really?") == [
        "One thing.",
        "Two things!",
        "Really?",
    ]


def test_estimate_minutes():
    assert estimate_minutes(155) == 1.0


def test_chunk_basic_two_sections():
    doc = Document(
        title="T",
        author="A",
        sections=[
            Section("Introduction", ["Hello world. Good day."]),
            Section("The Body", ["Another paragraph here."]),
        ],
    )
    chs = chunk_document(doc)
    assert len(chs) == 2
    assert chs[0].index == 1
    assert chs[0].segments[0] == "Introduction."
    assert "Hello world." in chs[0].segments
    assert chs[1].segments[0] == "The Body."


def test_chunk_subsplits_long_section():
    big = " ".join(["word"] * 200) + "."
    doc = Document(title="T", author="A", sections=[Section("Long", [big, big, big, big])])
    chs = chunk_document(doc, max_min=1)  # 155-word limit
    assert len(chs) >= 4
    assert chs[1].title == "Long (continued)"
