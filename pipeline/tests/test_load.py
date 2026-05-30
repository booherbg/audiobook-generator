from pipeline.load import HTMLLoader
from pipeline.model import Document


def test_html_loader_structure(tmp_path):
    html = (
        "<html><head><title>My Doc</title></head><body>"
        "<h2>Introduction</h2><p>First para[1].</p><p>Second para.</p>"
        "<h2>The Body</h2><p>Third para.</p></body></html>"
    )
    f = tmp_path / "s.html"
    f.write_text(html)
    doc = HTMLLoader().load(str(f))
    assert isinstance(doc, Document)
    assert doc.title == "My Doc"
    assert len(doc.sections) == 2
    assert doc.sections[0].heading == "Introduction"
    assert doc.sections[0].paragraphs == ["First para[1].", "Second para."]
    assert doc.sections[1].heading == "The Body"


def test_html_loader_vatican_style(tmp_path):
    html = (
        '<html><head><title>Enc</title></head><body>'
        '<p class="MsoNormal">ENCYCLICAL LETTER</p>'
        '<p class="MsoNormal">MAGNIFICA HUMANITAS</p>'
        '<p class="MsoNormal">INTRODUCTION</p>'
        '<p class="MsoNormal">First intro paragraph.<sup>1</sup></p>'
        '<p class="MsoNormal">CHAPTER I</p>'
        '<p class="MsoNormal">THE HUMAN PERSON IN AN AGE OF MACHINES</p>'
        '<p class="MsoNormal">Body of chapter one here.</p>'
        '<p class="MsoFootnoteText">1. some footnote</p>'
        '<p class="MsoNormal">CONCLUSION</p>'
        '<p class="MsoNormal">Final words.</p>'
        "</body></html>"
    )
    f = tmp_path / "v.html"
    f.write_text(html)
    doc = HTMLLoader().load(str(f))
    assert [s.heading for s in doc.sections] == [
        "Introduction",
        "The Human Person in an Age of Machines",
        "Conclusion",
    ]
    assert doc.sections[0].paragraphs == ["First intro paragraph."]
    assert doc.sections[1].paragraphs == ["Body of chapter one here."]
    assert doc.sections[2].paragraphs == ["Final words."]
