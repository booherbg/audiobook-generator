"""Read/insert/save the static player's manifest.json (the pipeline⇄player interface)."""

import json
from pathlib import Path


def empty_manifest() -> dict:
    return {"version": 1, "books": []}


def load_manifest(path: Path) -> dict:
    path = Path(path)
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return empty_manifest()


def insert_book(manifest: dict, book: dict) -> dict:
    """Add or replace a book by id (idempotent re-generation)."""
    books = [b for b in manifest.get("books", []) if b.get("id") != book["id"]]
    books.append(book)
    manifest["books"] = books
    return manifest


def save_manifest(path: Path, manifest: dict) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
