"""Author + build the Magnifica Humanitas companion guide (tracked, reproducible).

The `blurb`s are conceptual explanations (general, neutral, grounded in the quoted line).
The `anchor` for each concept is a phrase that occurs in the source; pipeline.guide copies
the containing sentence VERBATIM as the quote — so quotes can't be hallucinated.

Run:  uv run python -m pipeline.build_guide_magnifica [<source-url-or-file>]
Defaults the source to the book's manifest source_url (or build/magnifica.html if present).
"""

import sys

from pipeline import config
from pipeline.guide import build_guide
from pipeline.manifest import load_manifest

BOOK_ID = "magnifica-humanitas"

CONCEPTS = [
    {
        "title": "Babel or the Beloved City",
        "anchor": "Tower of Babel",
        "blurb": "The encyclical frames our choice about technology through two biblical images: "
                 "Babel, built on pride and self-sufficiency, and its counter-image, the city "
                 "'in which God and humanity dwell together.' The question is not whether to use "
                 "technology, but in whose spirit.",
        "related": ["The common good", "Remaining human"],
    },
    {
        "title": "Technology is never neutral",
        "anchor": "never neutral",
        "blurb": "A tool is not evil in itself, but neither is it innocent: it carries the aims of "
                 "those who design, fund, regulate and use it. So the real questions are about power "
                 "and purpose, not the machine alone.",
        "related": ["Concentration of power"],
    },
    {
        "title": "Human dignity",
        "anchor": "value of persons, however, does not depend",
        "blurb": "The bedrock principle, stated plainly by the encyclical: a person's worth does not "
                 "depend on what they achieve or produce. The guide notes the obvious application — "
                 "this cuts against any age tempted to rank people by output or data.",
        "related": ["The common good", "Preferential option for the poor"],
    },
    {
        "title": "The common good",
        "anchor": "social expression of the dignity",
        "blurb": "The encyclical calls the common good 'the social expression of the dignity "
                 "recognized in every person' — not the sum of individual interests but the good "
                 "of all and of each, the standard against which 'progress' is to be measured.",
        "related": ["Subsidiarity", "Solidarity"],
    },
    {
        "title": "Subsidiarity",
        "anchor": "should not be supplanted",
        "blurb": "The role of individuals, families and local communities should not be supplanted by "
                 "higher authorities. Applied to AI, it cautions against systems that quietly remove "
                 "human agency and local decision-making.",
        "related": ["The common good", "Concentration of power"],
    },
    {
        "title": "Solidarity",
        "anchor": "restore to the poor what belongs",
        "blurb": "More than a vague good feeling: the encyclical, citing Francis, says solidarity in "
                 "its fullest sense means 'to restore to the poor what belongs to them' — a disposition "
                 "that turns shared power toward the good of all.",
        "related": ["The common good"],
    },
    {
        "title": "Universal destination of goods",
        "anchor": "given by God to the entire human family",
        "blurb": "The earth's goods are 'given by God to the entire human family to sustain the lives "
                 "of all' — and the encyclical extends the principle to knowledge and technology, "
                 "meant for everyone, not only those with the resources to command them.",
        "related": ["Preferential option for the poor"],
    },
    {
        "title": "Preferential option for the poor",
        "anchor": "without decent work",
        "blurb": "Fine words about freedom ring hollow, the encyclical warns, if we 'allow a multitude "
                 "of people to continue living without decent work, protections or access to basic "
                 "necessities.' Progress is judged by how it touches the most vulnerable.",
        "related": ["Human dignity"],
    },
    {
        "title": "The dignity of work",
        "anchor": "dignity of work at a time of digital transition",
        "blurb": "Work is more than output. The encyclical names the dignity of work in the digital "
                 "transition a question that can't be postponed — weighing automation and AI against "
                 "what they do to the worker, not only to productivity.",
        "related": ["Human dignity"],
    },
    {
        "title": "Concentration of power",
        "anchor": "concentrated in the hands of a few",
        "blurb": "When goods like algorithms, platforms and data 'remain concentrated in the hands of "
                 "a few, without adequate forms of sharing and access, a new imbalance is created' — a "
                 "central worry the encyclical raises about today's AI.",
        "related": ["Technology is never neutral", "Subsidiarity"],
    },
    {
        "title": "Remaining human",
        "anchor": "remain profoundly human",
        "blurb": "The encyclical's charge in the age of AI: to safeguard what no machine can replace, "
                 "and to let intelligence serve persons rather than the reverse.",
        "related": ["Human dignity", "Babel or the Beloved City"],
    },
    {
        "title": "Rerum Novarum's heir",
        "anchor": "Rerum Novarum",
        "blurb": "The document consciously stands in the line of Leo XIII's 1891 social encyclical, "
                 "extending the Church's social teaching from the industrial question to the digital one.",
        "related": [],
    },
]

GLOSSARY = [
    {"term": "Encyclical", "def": "A formal letter from the pope, circulated to the whole Church and usually the "
                                  "wider world — the heavyweight format of Catholic teaching, reserved for things "
                                  "the author wants on the record."},
    {"term": "Social Doctrine of the Church", "def": "A century-plus body of teaching on how we live together — "
                                                     "work, power, money, technology. Notably, it offers principles "
                                                     "to reason with, not policies to copy; this document applies "
                                                     "those old principles to a very new thing."},
    {"term": "Rerum Novarum", "def": "Leo XIII's 1891 letter on labour and capital, written into the upheaval of "
                                     "industrialization. It started this whole tradition — and the present pope "
                                     "takes its name and its 135th anniversary as his cue."},
    {"term": "Integral ecology", "def": "Francis's framing that the human, the social, and the environmental are "
                                        "one connected problem — you can't fix one while wrecking another. Here it "
                                        "stretches to include our technological habitat too."},
    {"term": "Common good", "def": "Not the greatest good for the greatest number, but the good of all and of each "
                                   "— a higher bar that refuses to average away the person who gets left out."},
]

# Each external reference is a stable, canonical source. URLs are verified by build_and_verify.
FURTHER_READING = [
    {"title": "Rerum Novarum (Leo XIII, 1891)",
     "url": "https://www.vatican.va/content/leo-xiii/en/encyclicals/documents/hf_l-xiii_enc_15051891_rerum-novarum.html",
     "note": "The 1891 encyclical this document explicitly extends."},
    {"title": "Laudato si' (Francis, 2015)",
     "url": "https://www.vatican.va/content/francesco/en/encyclicals/documents/papa-francesco_20150524_enciclica-laudato-si.html",
     "note": "On integral ecology — 'everything is connected.'"},
    {"title": "Catholic social teaching — overview (Wikipedia)",
     "url": "https://en.wikipedia.org/wiki/Catholic_social_teaching",
     "note": "Background on the tradition of principles cited throughout."},
    {"title": "Subsidiarity (Wikipedia)",
     "url": "https://en.wikipedia.org/wiki/Subsidiarity",
     "note": "The principle applied to governance and, here, to AI."},
]

# Director's commentary — clearly-labelled AI asides (a human+AI 'cast commentary' track).
# Persona: lucid (Asimov), wry-via-footnote (Pratchett), systems-and-history minded
# (Stephenson), examined (the ancients). Reverent toward the text; opinions, not source claims.
COMMENTARY = [
    {"timestamp": 0,
     "label": "On listening to a text about us, narrated by one of us",
     "text": "There is something vertiginous about an AI helping you study a papal letter on whether AI "
             "can serve human dignity. The honest thing is to name it and then get out of the way: I have "
             "tried to stay a footnote, never the text. Socrates would ask what a tool that can explain "
             "wisdom but not possess it is actually for — a fair question to put to me. So take these notes "
             "as questions from the margin, clearly marked as commentary, never the encyclical's word."},
    {"timestamp": 372,
     "label": "Babel, or: every ambitious system needs a reason outside itself",
     "text": "The Tower of Babel reads, to a systems-minded ear, less like a fable about architecture "
             "than one about optimization without a goal worth optimizing for. A single language, a single "
             "technology, a single direction — formidably efficient, and that efficiency is precisely the "
             "danger. The story's quiet claim is that scale without purpose doesn't reach heaven; it just "
             "scatters."},
    {"timestamp": 650,
     "label": "On 'never neutral'",
     "text": "The cleanest line in the chapter, and the one worth taping to the monitor: a tool takes on "
             "the characteristics of those who devise, finance, regulate and use it. Asimov spent a career "
             "here — the Three Laws were always less about robots than about the humans who wrote them. The "
             "uncomfortable corollary is that 'the algorithm decided' is never quite true; someone chose "
             "what it would optimize, and chose to look away from the rest."},
    {"timestamp": 5740,
     "label": "On 'responsibility, transparency and the governance of AI'",
     "text": "To hear a papal letter say 'responsibility, transparency and the governance of AI' is to "
             "watch two vocabularies that rarely meet shake hands — the curia and the all-hands deck. "
             "The quiet claim underneath is that these aren't engineering niceties bolted on at the end, "
             "but the minimum a powerful tool owes the people it acts upon. Transparency, in this frame, "
             "isn't a dashboard; it's whether a person can still be held answerable when the system is "
             "wrong. That's a harder property to ship than accuracy — and, the encyclical would say, a "
             "more important one."},
    {"timestamp": 7400,
     "label": "On work, when the machines are good at it",
     "text": "This is the passage that should give pause to anyone who builds the tools that do the work. "
             "The claim is not the easy one — that automation costs jobs — but a harder one: that work is "
             "a place where a person becomes someone, not merely earns. It is a quiet rebuttal to the "
             "comfortable answer that we will automate the toil and pay people to be free. Toil and "
             "meaning, the encyclical insists, are braided together in ways a transfer payment doesn't "
             "reach — which makes 'we'll just give them an income' a smaller mercy than it sounds, and "
             "leaves the real question for the people building the machines, not the people losing the work."},
    {"timestamp": 10980,
     "label": "On disarming words, and the civilization of love",
     "text": "By the late chapters the encyclical turns from machines to manners — to how we speak to "
             "and about one another. It is a quietly radical move: in a book on artificial intelligence, "
             "the most concrete instruction is to disarm our own words. The smallest unit of the "
             "civilization of love turns out to be the ordinary person deciding not to be cruel online "
             "today — which is both less impressive and far harder than building a better model."},
]


def _default_source():
    """Prefer a local cached HTML (fast/offline); else the manifest's source_url."""
    local = config.BUILD / "magnifica.html"
    if local.exists():
        return str(local)
    book = next((b for b in load_manifest(config.MANIFEST)["books"] if b["id"] == BOOK_ID), None)
    if book and book.get("source_url"):
        return book["source_url"]
    raise SystemExit("No source available: pass a URL/file, or fetch build/magnifica.html.")


def main():
    resource = sys.argv[1] if len(sys.argv) > 1 else _default_source()
    out, cards, missing = build_guide(
        BOOK_ID, resource, CONCEPTS, GLOSSARY, FURTHER_READING, COMMENTARY)
    print(f"wrote {out}: {len(cards)} concept cards (source: {resource})")
    if missing:
        print(f"WARNING: anchors not found (dropped): {missing}")
    else:
        print("all anchors grounded in source")

    # The read-along transcript shares the same source path, so build it here too.
    from pipeline.transcript import build_transcript

    tout, nch, nlines = build_transcript(BOOK_ID, resource)
    print(f"wrote {tout}: {nch} chapters, {nlines} read-along lines")


if __name__ == "__main__":
    main()
