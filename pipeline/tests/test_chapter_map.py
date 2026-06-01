from pipeline.chapter_map import resection
from pipeline.model import Document, Section


def _doc():
    # One blob of paragraphs, the way an unstructured encyclical loads.
    return Document(
        title="T", author="A",
        sections=[Section("", ["Intro front matter.", "Para A about property.",
                               "Para B continues.", "Para C about the family.",
                               "Para D continues."])],
    )


def test_resection_splits_by_anchor():
    cmap = [{"title": "Property", "anchor": "Para A"},
            {"title": "The Family", "anchor": "Para C"}]
    doc = resection(_doc(), cmap)
    assert [s.heading for s in doc.sections] == ["Property", "The Family"]
    # Front matter before the first anchor folds into chapter 1.
    assert doc.sections[0].paragraphs == ["Intro front matter.", "Para A about property.", "Para B continues."]
    assert doc.sections[1].paragraphs == ["Para C about the family.", "Para D continues."]


def test_resection_is_case_insensitive_and_sequential():
    # Same word "continues" appears twice; anchors resolve in order, each after the previous.
    cmap = [{"title": "One", "anchor": "para a"},
            {"title": "Two", "anchor": "continues"},
            {"title": "Three", "anchor": "para c"}]
    doc = resection(_doc(), cmap)
    assert [s.heading for s in doc.sections] == ["One", "Two", "Three"]
    assert doc.sections[1].paragraphs == ["Para B continues."]   # first "continues" after Para A
    assert doc.sections[2].paragraphs == ["Para C about the family.", "Para D continues."]


def test_resection_missing_anchor_raises():
    try:
        resection(_doc(), [{"title": "X", "anchor": "no such phrase"}])
    except ValueError as e:
        assert "no such phrase" in str(e)
    else:
        raise AssertionError("expected ValueError for a missing anchor")
