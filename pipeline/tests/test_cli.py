from pipeline.__main__ import clean_document, slugify
from pipeline.model import Document, Section


def test_slugify():
    assert slugify("Magnifica Humanitas") == "magnifica-humanitas"
    assert slugify("Hello, World!") == "hello-world"
    assert slugify("  multiple   spaces ") == "multiple-spaces"
    assert slugify("") == "book"


def test_clean_document_drops_boilerplate_and_empty():
    doc = Document(
        title="T",
        author="A",
        sections=[
            Section("S1", ["Real paragraph.", "Copyright © Dicastero per la Comunicazione", "   "]),
            Section("S2", ["  ", ""]),
        ],
    )
    clean_document(doc)
    assert len(doc.sections) == 1
    assert doc.sections[0].paragraphs == ["Real paragraph."]
