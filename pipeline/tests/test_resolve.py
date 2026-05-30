import pytest

from pipeline.resolve import ResolveError, resolve


def test_resolve_url_passthrough():
    assert resolve("https://example.com/x") == "https://example.com/x"
    assert resolve("http://example.com/x") == "http://example.com/x"


def test_resolve_existing_file(tmp_path):
    f = tmp_path / "doc.html"
    f.write_text("<html></html>")
    assert resolve(str(f)) == str(f)


def test_resolve_description_errors():
    with pytest.raises(ResolveError) as exc:
        resolve("the pope's AI encyclical")
    assert "Ask Claude Code" in str(exc.value)
