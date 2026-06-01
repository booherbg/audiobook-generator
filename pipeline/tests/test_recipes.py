"""Every book recipe (data/books/<id>.json) must be valid and self-contained, so a book
can be regenerated from git alone — audio as a build artifact, not a precious snapshot."""

import json

from pipeline import config

RECIPES = sorted((config.ROOT / "data" / "books").glob("*.json"))


def test_recipes_exist():
    assert RECIPES, "expected at least one book recipe in data/books/"


def test_each_recipe_is_complete_and_its_files_exist():
    required = {"id", "title", "author", "source_url", "rights", "voices", "guide_builder"}
    for path in RECIPES:
        r = json.loads(path.read_text())
        missing = required - r.keys()
        assert not missing, f"{path.name}: missing required keys {missing}"
        assert r["id"] == path.stem, f"{path.name}: id must match filename"
        assert isinstance(r["voices"], list) and r["voices"], f"{path.name}: voices must be non-empty"

        # Referenced files must actually exist (this is what makes regeneration reproducible).
        for key in ("source_file", "chapter_map", "repairs"):
            ref = r.get(key)
            if ref:
                assert (config.ROOT / ref).exists(), f"{path.name}: {key} -> missing file {ref}"

        # A committed source snapshot is what guarantees offline, vatican.va-independent rebuilds.
        assert r.get("source_file"), f"{path.name}: should pin a committed source_file snapshot"

        # The guide builder module must be importable and expose main().
        import importlib

        mod = importlib.import_module(r["guide_builder"])
        assert hasattr(mod, "main"), f"{r['guide_builder']} must expose main()"
