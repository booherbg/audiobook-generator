"""Regression test: rebuilding the manifest must preserve every voice present on disk,
even when a generate run targeted only one voice (the bug that dropped 'female' from the
shipped manifest after a male-only re-render)."""

import json
from types import SimpleNamespace

from pipeline.__main__ import _write_manifest
from pipeline.model import Chapter


def _make_audio(audio_root, book_id, voices, n_chapters):
    for v in voices:
        d = audio_root / book_id / v
        d.mkdir(parents=True, exist_ok=True)
        for i in range(1, n_chapters + 1):
            (d / f"chapter-{i:02d}.mp3").write_bytes(b"\x00" * 2000)  # >1000 bytes


def test_write_manifest_keeps_all_voices_on_single_voice_run(tmp_path, monkeypatch):
    from pipeline import config, __main__ as M

    monkeypatch.setattr(config, "DOCS", tmp_path)
    monkeypatch.setattr(config, "AUDIO_ROOT", tmp_path / "audio")
    monkeypatch.setattr(config, "MANIFEST", tmp_path / "manifest.json")

    book_id = "bk"
    voices_cfg = {"female": {"ref": "af", "label": "F"}, "male": {"ref": "am", "label": "M"}}
    chapters = [Chapter(index=i, title=f"C{i}", segments=["x"]) for i in (1, 2)]
    _make_audio(config.AUDIO_ROOT, book_id, ["female", "male"], 2)

    # Avoid real ffprobe: stub duration.
    monkeypatch.setattr(M, "probe", lambda p: {"duration": 12.3})

    # Simulate a run that only selected 'male' — manifest must still list BOTH voices.
    args = SimpleNamespace(subtitle="", author="", date="", description="", source_url="")
    _write_manifest(args, book_id, "Title", chapters, ["male"], voices_cfg, "http://x")

    m = json.loads((tmp_path / "manifest.json").read_text())
    book = m["books"][0]
    assert sorted(v["id"] for v in book["voices"]) == ["female", "male"]
    assert sorted(book["chapters"][0]["files"].keys()) == ["female", "male"]


def test_write_manifest_preserves_metadata_on_partial_rerender(tmp_path, monkeypatch):
    """A re-render that doesn't pass --subtitle/--date/etc must NOT wipe the book's existing
    metadata or flip has_guide/wip back to defaults (the footgun that blanked Magnifica's
    subtitle + date during a --force ch1 re-render)."""
    from pipeline import config, __main__ as M

    monkeypatch.setattr(config, "DOCS", tmp_path)
    monkeypatch.setattr(config, "AUDIO_ROOT", tmp_path / "audio")
    monkeypatch.setattr(config, "MANIFEST", tmp_path / "manifest.json")
    monkeypatch.setattr(M, "probe", lambda p: {"duration": 12.3})

    book_id = "bk"
    voices_cfg = {"george": {"ref": "bm_george", "label": "George"}}
    chapters = [Chapter(index=1, title="C1", segments=["x"])]
    _make_audio(config.AUDIO_ROOT, book_id, ["george"], 1)

    # First: a full generate establishing metadata + flags.
    full = SimpleNamespace(subtitle="On Capital and Labor", author="Pope Leo XIII",
                           date="1891", description="d", source_url="http://vatican/rn")
    _write_manifest(full, book_id, "Rerum Novarum", chapters, ["george"], voices_cfg, "http://vatican/rn")
    m = json.loads((tmp_path / "manifest.json").read_text())
    # simulate companion + WIP flags being set after generate
    m["books"][0]["has_guide"] = True
    m["books"][0]["wip"] = True
    (tmp_path / "manifest.json").write_text(json.dumps(m))

    # Then: a partial re-render with EMPTY metadata args (the footgun scenario).
    bare = SimpleNamespace(subtitle="", author="", date="", description="", source_url="")
    _write_manifest(bare, book_id, "Rerum Novarum", chapters, ["george"], voices_cfg, "build/rn.html")

    book = json.loads((tmp_path / "manifest.json").read_text())["books"][0]
    assert book["subtitle"] == "On Capital and Labor", "subtitle must survive a bare re-render"
    assert book["author"] == "Pope Leo XIII"
    assert book["date"] == "1891"
    assert book["has_guide"] is True, "has_guide must not be reset to False"
    assert book.get("wip") is True, "wip flag must be preserved"
