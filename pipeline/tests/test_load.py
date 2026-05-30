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
