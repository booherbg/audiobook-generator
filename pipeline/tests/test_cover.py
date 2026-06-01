"""Default cover generation: valid SVG, never overwrites a hand-made cover."""

import xml.dom.minidom

from pipeline import cover


def test_default_cover_is_well_formed_svg():
    xml.dom.minidom.parseString(cover._svg("Rerum Novarum", "Pope Leo XIII", "On capital and labor"))


def test_long_title_wraps_to_two_lines_short_stays_one():
    assert len(cover._title_lines("Short")) == 1
    assert len(cover._title_lines("Magnifica Humanitas")) == 2


def test_title_with_special_chars_is_escaped():
    svg = cover._svg("A & B <C>", "x", "y")
    assert "&amp;" in svg and "&lt;" in svg
    xml.dom.minidom.parseString(svg)  # still well-formed


def test_ensure_cover_does_not_overwrite_existing(tmp_path, monkeypatch):
    monkeypatch.setattr(cover.config, "AUDIO_ROOT", tmp_path)
    book = tmp_path / "bk"
    book.mkdir()
    (book / "cover.svg").write_text("HANDMADE")
    out, created = cover.ensure_cover("bk", "Title", "Author", "Sub")
    assert created is False
    assert out.read_text() == "HANDMADE"


def test_ensure_cover_creates_when_missing(tmp_path, monkeypatch):
    monkeypatch.setattr(cover.config, "AUDIO_ROOT", tmp_path)
    out, created = cover.ensure_cover("bk", "Title", "Author", "Sub")
    assert created is True
    assert out.exists()
    xml.dom.minidom.parseString(out.read_text())
