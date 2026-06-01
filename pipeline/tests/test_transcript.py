"""Transcript generator: lines must come verbatim from the source and start-fractions
must be ascending in [0,1) so the player can highlight/seek correctly."""

import json

from pipeline import transcript as T


def test_build_transcript(tmp_path, monkeypatch):
    monkeypatch.setattr(T, "TRANSCRIPT_DIR", tmp_path)

    fake_chapters = [
        (1, "Introduction", ["Introduction.", "First sentence here.", "Second one follows."]),
        (2, "The Body", ["The Body.", "Only line."]),
    ]
    monkeypatch.setattr(T, "clean_chapters",
                        lambda resource, chapter_map=None, repairs=None: fake_chapters)

    out, nch, nlines = T.build_transcript("bk", "ignored")
    assert nch == 2 and nlines == 5

    data = json.loads(out.read_text())
    c0 = data["chapters"][0]
    assert c0["title"] == "Introduction"
    assert c0["lines"] == ["Introduction.", "First sentence here.", "Second one follows."]
    # starts ascending, first is 0, all in [0,1)
    assert c0["starts"][0] == 0
    assert all(0 <= x < 1 for x in c0["starts"])
    assert c0["starts"] == sorted(c0["starts"])
    assert len(c0["starts"]) == len(c0["lines"])
