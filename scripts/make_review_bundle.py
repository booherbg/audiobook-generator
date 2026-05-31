"""Flatten a built companion guide into readable markdown for the critic panel.

Usage: python scripts/make_review_bundle.py <book-id>

Writes build/companion_for_review.md so critic subagents read exactly what ships
(the built guide JSON), not the authoring intent. See docs/playbook/critic-panel.md.
"""

import json
import sys

from pipeline import config


def main():
    book = sys.argv[1] if len(sys.argv) > 1 else "magnifica-humanitas"
    g = json.loads((config.DOCS / "guide" / f"{book}.json").read_text())

    out = [f"# COMPANION: {book}\n", "## INTRO\n" + g["intro"], "\n## CONCEPT CARDS"]
    for c in g["concepts"]:
        out.append(f"\n### {c['title']} [ch{c['chapter']}]\n"
                   f"BLURB: {c['blurb']}\nQUOTE: “{c['quote']}”")
    out.append("\n## COMMENTARY")
    for c in g["commentary"]:
        out.append(f"\n### {c['label']} [ch{c['chapter']}]\n{c['text']}")
    out.append("\n## GLOSSARY\n" + "\n".join(f"- {t['term']}: {t['def']}" for t in g["glossary"]))

    dest = config.BUILD / "companion_for_review.md"
    dest.write_text("\n".join(out), encoding="utf-8")
    print(f"wrote {dest} ({len(g['concepts'])} concepts)")


if __name__ == "__main__":
    main()
