"""Validate a companion guide JSON against its source: quotes verbatim, links live.

Usage: python scripts/validate_guide.py <book-id> [source]

Checks every concept quote is an exact substring of the cleaned source text, every
cross-link resolves to a real card, and titles are unique. Exits non-zero on any failure
so CI / the checklist / the playbook can gate on it. See docs/playbook/qa-audit.md.
"""

import json
import re
import sys

from pipeline import config
from pipeline.source_text import clean_chapters


def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def _optional_json(path):
    return json.loads(path.read_text()) if path.exists() else None


def main():
    book = sys.argv[1] if len(sys.argv) > 1 else "magnifica-humanitas"
    src = sys.argv[2] if len(sys.argv) > 2 else str(config.BUILD / "magnifica.html")

    # Use the same chapter map + repairs the guide was built with (auto-discovered by id),
    # so the reference text matches exactly what the quotes were extracted from.
    cmap = _optional_json(config.ROOT / "data" / "chapter_maps" / f"{book}.json")
    repairs = _optional_json(config.ROOT / "data" / "repairs" / f"{book}.json")

    g = json.loads((config.DOCS / "guide" / f"{book}.json").read_text())
    text = " ".join(s for _, _, lines in clean_chapters(src, chapter_map=cmap, repairs=repairs)
                    for s in lines)
    ids = {slug(c["title"]) for c in g["concepts"]}

    nonverbatim = [c["title"] for c in g["concepts"] if c["quote"].strip("“”\"'") not in text]
    dead = [(c["title"], r) for c in g["concepts"]
            for r in c.get("related", []) if slug(r) not in ids]
    titles = [c["title"] for c in g["concepts"]]
    dup = len(titles) != len(set(titles))

    ok = not nonverbatim and not dead and not dup
    print(f"{book}: concepts={len(g['concepts'])} "
          f"nonverbatim={nonverbatim or 'NONE'} dead={dead or 'NONE'} "
          f"unique_titles={not dup}")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
