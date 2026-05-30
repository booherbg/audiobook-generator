from pipeline.manifest import empty_manifest, insert_book, load_manifest, save_manifest


def test_insert_replaces_by_id():
    m = empty_manifest()
    insert_book(m, {"id": "a", "title": "A1"})
    insert_book(m, {"id": "a", "title": "A2"})
    insert_book(m, {"id": "b", "title": "B"})
    ids = [b["id"] for b in m["books"]]
    assert ids.count("a") == 1
    assert next(b for b in m["books"] if b["id"] == "a")["title"] == "A2"
    assert "b" in ids


def test_round_trip(tmp_path):
    m = empty_manifest()
    insert_book(
        m,
        {
            "id": "x",
            "title": "X",
            "chapters": [{"index": 1, "files": {"female": "f.mp3"}, "duration": {"female": 10}}],
        },
    )
    p = tmp_path / "manifest.json"
    save_manifest(p, m)
    m2 = load_manifest(p)
    assert m2["books"][0]["chapters"][0]["duration"]["female"] == 10


def test_load_missing_returns_empty(tmp_path):
    assert load_manifest(tmp_path / "nope.json") == empty_manifest()
