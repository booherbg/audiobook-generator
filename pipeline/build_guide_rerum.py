"""Author + build the Rerum Novarum companion guide (tracked, reproducible).

Same contract as build_guide_magnifica: `blurb`s are conceptual explanations; each `anchor`
is a VERBATIM phrase in the source and pipeline.guide copies the containing sentence as the
quote, so quotes cannot be hallucinated. Director's commentary is clearly-labelled AI opinion.

Run:  .venv/bin/python -m pipeline.build_guide_rerum
Source defaults to build/rerum-novarum.html; uses the same chapter map + repairs as the audio,
so concept chapters/fractions line up with the narration.
"""

import json
import sys

from pipeline import config
from pipeline.guide import build_guide
from pipeline.manifest import load_manifest
from pipeline.transcript import build_transcript
from pipeline.fulltext import build_fulltext

BOOK_ID = "rerum-novarum"
CHAPTER_MAP = config.ROOT / "data" / "chapter_maps" / "rerum-novarum.json"
REPAIRS = config.ROOT / "data" / "repairs" / "rerum-novarum.json"

INTRO = (
    "A companion to the reading — not a replacement for it. This is the document that began "
    "modern Catholic social teaching: in 1891, with the factory and the slum remaking Europe, "
    "Leo XIII tried to think clearly about work, property, and the worker. There is a quiet "
    "rhyme in reading it now, in a second machine age, with the help of a machine. Everything "
    "below points back to the text in the author's own words — each quotation is verbatim — and "
    "every opinion is labelled as mine, not his. Pull a thread if you're curious; close the tab "
    "and just listen if you're not."
)

# Concepts RN originates — the seeds the later tradition (and Magnifica) grows from.
CONCEPTS = [
    {
        "title": "The condition of the workers",
        "anchor": "some opportune remedy must be found quickly for the misery and wretchedness",
        "blurb": "The encyclical's starting point is not theory but a wound: the real misery of "
                 "working people — which Leo XIII lays at the door of the old guilds' abolition with "
                 "nothing put in their place. He writes into the upheaval of industrialization, and "
                 "he refuses to look away from it. Everything that follows is an attempt to answer "
                 "this suffering justly.",
        "related": ["The false remedy of socialism", "The State's special care for the poor"],
    },
    {
        "title": "The false remedy of socialism",
        "anchor": "striving to do away with private property",
        "blurb": "Leo XIII takes socialism seriously enough to argue against it at length. His "
                 "objection is practical and moral at once: abolishing private property would rob "
                 "the very worker it claims to help — of the fruit of his labour and the hope of "
                 "bettering his lot — and hand dangerous power to the State. The remedy, he says, "
                 "is worse than the disease.",
        "related": ["The condition of the workers", "Property as a natural right"],
    },
    {
        "title": "Property as a natural right",
        "anchor": "every man has by nature the right to possess property as his own",
        "blurb": "The hinge of the whole letter. Because a person reasons, plans for the future, "
                 "and works deliberately, the fruit of that labour — and the means to secure it — "
                 "is rightly his own. Property is not a mere social convention to be redistributed "
                 "at will; it answers something in human nature. Crucially, Leo XIII does not stop "
                 "there: in the same breath he holds that owned goods still serve everyone (see "
                 "'Goods are meant for all'). Both truths at once — the right is real, and it is not "
                 "absolute.",
        "related": ["The false remedy of socialism", "Goods are meant for all", "Property and the family", "A living wage"],
    },
    {
        "title": "Goods are meant for all",
        "anchor": "ceases not thereby to minister to the needs of all",
        "blurb": "The counterweight to private property — and, crucially, it is in Rerum Novarum "
                 "itself, not a later correction. Quoting Aquinas, Leo XIII teaches that a person may "
                 "rightly own things, yet 'should not consider his material possessions as his own, "
                 "but as common to all, so as to share them without hesitation when others are in "
                 "need.' Ownership is real; its use is owed. This is what later teaching calls the "
                 "universal destination of goods — and the seed Magnifica Humanitas carries forward.",
        "related": ["Property as a natural right", "The truth about wealth"],
    },
    {
        "title": "Property and the family",
        "anchor": "It is a most sacred law of nature that a father should provide",
        "blurb": "Leo XIII roots property in the family before the State: a father must be able to "
                 "provide for and pass something on to his children. The family is a true society, "
                 "older than the commonwealth, with rights the State must respect, not absorb. This "
                 "is the seed of subsidiarity — the principle that larger bodies should help, not "
                 "swallow, the smaller communities closest to the person.",
        "related": ["Property as a natural right", "The State's special care for the poor"],
    },
    {
        "title": "Neither class the enemy of the other",
        "anchor": "intended by nature to live in mutual conflict",
        "blurb": "Against the idea that capital and labour are natural enemies, Leo XIII insists "
                 "the opposite: 'Each needs the other: capital cannot do without labor, nor labor "
                 "without capital.' Justice and shared interest, not class war, are the way through. "
                 "It is a direct answer to the socialism of its moment — and an old idea, that the "
                 "parts of a body do not war on one another.",
        "related": ["The mutual duties of capital and labor", "The dignity of labor"],
    },
    {
        "title": "The mutual duties of capital and labor",
        "anchor": "Of these duties, the following bind the proletarian and the worker",
        "blurb": "Leo XIII spells out obligations on both sides — the worker to give honest work "
                 "and keep agreements; the employer never to treat workers as mere means, to leave "
                 "time for family and faith, and above all to pay a just wage. Rights come paired "
                 "with duties; this is the texture of a just workplace, not a slogan.",
        "related": ["Neither class the enemy of the other", "A living wage", "The dignity of labor"],
    },
    {
        "title": "The dignity of labor",
        "anchor": "in God's sight poverty is no disgrace",
        "blurb": "Work is not a curse to be escaped nor a mark of low birth; honest labour is "
                 "honourable, and poverty is no shame in God's sight. Christ himself worked with his "
                 "hands. The worker's worth does not rise or fall with his wealth — a thread that "
                 "runs straight to the later teaching on the dignity of the person.",
        "related": ["The truth about wealth", "A living wage"],
    },
    {
        "title": "The truth about wealth",
        "anchor": "it becomes a duty to give to the indigent out of what remains over",
        "blurb": "To the rich, Leo XIII is blunt: ownership is lawful, but once your needs and "
                 "your station are fairly provided for, what remains is owed — as a duty of "
                 "charity, and in hard cases of justice — to those who lack. Wealth is a "
                 "stewardship, and Leo frames it before the eternal Judge: a strict account will be "
                 "asked of how it was used.",
        "related": ["Goods are meant for all", "The dignity of labor", "The State's special care for the poor"],
    },
    {
        "title": "A living wage",
        "anchor": "wages ought not to be insufficient to support a frugal and well-behaved",
        "blurb": "The encyclical's most famous claim, and its boldest: beneath any free bargain over "
                 "pay lies 'a dictate of natural justice more imperious and ancient than any bargain "
                 "between man and man' — that a wage must be enough for a frugal worker to live, "
                 "support a family, and even save toward owning something himself. Note the ground: "
                 "not mere need or market economics, but a moral law that binds prior to any "
                 "contract. And the wage points somewhere — toward the worker one day owning a stake "
                 "of his own.",
        "related": ["The mutual duties of capital and labor", "Property as a natural right", "The dignity of labor"],
    },
    {
        "title": "The State's special care for the poor",
        "anchor": "the mass of the poor have no resources of their own to fall back upon",
        "blurb": "The State exists for the common good of all — but precisely because the rich can "
                 "shield themselves and the poor cannot, public authority owes the vulnerable a "
                 "particular care. Here, in 1891, is the root of what later teaching will call the "
                 "preferential option for the poor.",
        "related": ["The truth about wealth", "The condition of the workers", "Property and the family"],
    },
    {
        "title": "Rest, and the rights of God",
        "anchor": "No man may with impunity outrage that human dignity which God Himself treats",
        "blurb": "Here is the encyclical's deepest grounding of the worker's dignity — and it is "
                 "frankly religious. The case for limiting hours and for Sunday rest is not only "
                 "humane fatigue management: the worker has a soul 'made after the image and likeness "
                 "of God,' and so 'no man may with impunity outrage that human dignity which God "
                 "Himself treats with great reverence.' Rest is owed to the person because the person "
                 "is owed to God. This is the bedrock the later talk of 'the dignity of the person' "
                 "stands on.",
        "related": ["The dignity of labor", "The mutual duties of capital and labor"],
    },
    {
        "title": "The right to associate",
        "anchor": "The most important of all are workingmen's unions",
        "blurb": "Leo XIII defends the natural right of workers to form unions and associations — "
                 "and, in his telling, looks back to the old craft guilds as their forerunners "
                 "(historians would add that those guilds were also exclusive, restrictive bodies, "
                 "and that unions and friendly societies were already growing by 1891). To band "
                 "together for the common good is a right that flows from human nature, and the "
                 "State may regulate such societies but not forbid them. Note, too, that the unions "
                 "Leo most commends are explicitly Christian ones.",
        "related": ["Neither class the enemy of the other", "The mutual duties of capital and labor"],
    },
    {
        "title": "The Church's claim to be heard",
        "anchor": "no practical solution of this question will be found apart from",
        "blurb": "Leo XIII stakes a claim that still provokes: that the social question cannot be "
                 "solved by economics and law alone, without religion and the Church. Whether or not "
                 "one shares the premise, it frames the whole document — this is moral reasoning "
                 "about economic life, not policy mechanics.",
        "related": ["The condition of the workers"],
    },
]

GLOSSARY = [
    {"term": "Encyclical", "def": "A formal letter from the pope to the whole Church and the wider world — "
                                  "the heavyweight format of Catholic teaching. Rerum Novarum is the one that "
                                  "started the modern social tradition."},
    {"term": "Rerum Novarum", "def": "Latin for 'of new things' — the opening words, and so the title. It names "
                                     "the revolutionary 'new things' (industrial capitalism, mass labour, "
                                     "socialism) the letter sets out to address."},
    {"term": "Natural law", "def": "The idea that there is a moral order built into human nature and knowable by "
                                   "reason — so some things (like a worker's claim to a living wage) are just or "
                                   "unjust prior to any law or contract that says so."},
    {"term": "Distributive justice", "def": "The duty of those who govern the whole to deal fairly with every "
                                            "class alike. (Leo XIII grounds the State's *particular* care for the "
                                            "poor not in this alone, but in their defencelessness and the common "
                                            "good — the rich 'have many ways of shielding themselves.')"},
    {"term": "Subsidiarity (in seed)", "def": "The principle that the larger community should support, never "
                                              "absorb, the smaller ones closest to the person — family, "
                                              "association, town. Rerum Novarum plants it; Pius XI names it in 1931."},
    {"term": "The living (just) wage", "def": "A wage sufficient for a frugal worker to support himself and his "
                                              "family — owed as a matter of justice, not merely set by the market. "
                                              "Rerum Novarum's most cited contribution."},
    {"term": "Catholic social teaching", "def": "The body of moral teaching on how we live together — work, "
                                                "property, power, the poor — that this letter began and that runs "
                                                "through Pius XI, John Paul II, and Francis. (Its imagined "
                                                "continuation into the age of AI, Leo XIV's Magnifica Humanitas, is "
                                                "the companion volume in this library — a creative work, not an "
                                                "actual encyclical.)"},
    {"term": "Universal destination of goods", "def": "The principle that the world's goods are meant for everyone: "
                                                      "one may own property, yet must hold it 'as common to all' in "
                                                      "use, sharing from one's surplus. Rerum Novarum states it "
                                                      "outright (via Aquinas) — it is not a later addition."},
]

FURTHER_READING = [
    {"title": "Magnifica Humanitas (the companion volume in this library)",
     "url": "https://www.vatican.va/content/leo-xiv/en/encyclicals/documents/20260515-magnifica-humanitas.html",
     "note": "A creative continuation — not an actual encyclical — carrying Rerum Novarum's argument into the age of AI."},
    {"title": "Quadragesimo Anno (Pius XI, 1931)",
     "url": "https://www.vatican.va/content/pius-xi/en/encyclicals/documents/hf_p-xi_enc_19310515_quadragesimo-anno.html",
     "note": "Written for Rerum Novarum's 40th anniversary; it names the principle of subsidiarity."},
    {"title": "Catholic social teaching — overview (Wikipedia)",
     "url": "https://en.wikipedia.org/wiki/Catholic_social_teaching",
     "note": "The tradition this encyclical began, in context."},
    {"title": "Rerum Novarum (Wikipedia)",
     "url": "https://en.wikipedia.org/wiki/Rerum_novarum",
     "note": "Historical background: the 1891 context, reception, and influence."},
]

# Director's commentary — clearly-labelled AI asides. Persona: lucid (Asimov), wry-via-footnote
# (Pratchett), systems-and-history minded (Stephenson), examined (the ancients). Reverent toward
# the text; opinions, not source claims. timestamps are seconds on the (single) voice's timeline.
COMMENTARY = [
    {"timestamp": 0,
     "label": "On reading 1891 from the far side of the machine",
     "text": "There is a strange doubling in studying this letter with an AI. Rerum Novarum was "
             "written into the FIRST machine age — the loom, the foundry, the railway — when new "
             "technology had remade work faster than anyone could think about it. You are now in the "
             "second, and I am one of its 'new things.' Leo XIII's instinct was not to curse the "
             "machines or to worship them, but to ask the older question underneath: what is owed to "
             "the person who works? That question outlived the loom. It will outlive me. Treat these "
             "notes as a margin, never the text."},
    {"timestamp": 200,
     "label": "On arguing with the dead seriously",
     "text": "Notice that Leo XIII does not caricature socialism; he states it at its strongest and "
             "then answers it. In 1891 this was not abstract — Das Kapital was a generation old, the "
             "First International within living memory. What strikes a systems-minded reader is the "
             "shape of the argument: he grants the diagnosis (the workers are genuinely suffering) "
             "and contests the remedy (abolishing property). Agree or not, it is how you argue when "
             "you take both the problem and your opponent seriously — a habit worth keeping."},
    {"timestamp": 900,
     "label": "On the family as the first society",
     "text": "The move here is quietly radical: the family is older than the State, so the State may "
             "help it but not swallow it. Forty years later Pius XI gives this a name — subsidiarity "
             "— and it becomes one of the load-bearing beams of the whole tradition, the one Magnifica "
             "Humanitas leans on when it worries about power being concentrated too far from ordinary "
             "people. You are watching a principle get planted before it has its name."},
    {"timestamp": 3650,
     "label": "On the wage that the market cannot set",
     "text": "This is the passage everyone remembers, and rightly. Leo XIII says a free bargain over "
             "wages is real — and that beneath it runs something 'more imperious and ancient' than any "
             "bargain: a worker's wage must be enough to actually live on. An economist will note he is "
             "claiming there are limits a market price cannot legitimately cross. Whatever you think of "
             "the economics, hold onto the structure of the claim — that human need can outrank a price "
             "— because the argument over it is not remotely finished."},
    {"timestamp": 2650,
     "label": "On who the State is for",
     "text": "The line worth slowing down on: the rich 'have many ways of shielding themselves,' the "
             "poor do not — therefore the State owes the poor particular care. This is not yet called "
             "the 'preferential option for the poor' (that language is a century away) but it is "
             "unmistakably the same instinct. It is also, for a document often filed under "
             "'conservative,' a strikingly pointed thing to say to power."},
    {"timestamp": 4050,
     "label": "On the right to band together",
     "text": "Leo XIII reaches back to the medieval guilds to defend a thoroughly modern thing: the "
             "union. He grounds it where the encyclical grounds most things — in Aquinas and the "
             "natural law: to band together is a natural right, and a law only binds when it accords "
             "with 'the eternal law of God,' so the State may regulate such societies but not forbid "
             "them. It is a useful reminder that 'new things' are often old needs wearing new "
             "clothes, which is roughly the whole thesis of reading a 135-year-old letter on the day "
             "you happen to be talking to an AI."},
]


def _default_source():
    local = config.BUILD / "rerum-novarum.html"
    if local.exists():
        return str(local)
    book = next((b for b in load_manifest(config.MANIFEST)["books"] if b["id"] == BOOK_ID), None)
    if book and book.get("source_url"):
        return book["source_url"]
    raise SystemExit("No source available: fetch build/rerum-novarum.html or pass a URL/file.")


def main():
    resource = sys.argv[1] if len(sys.argv) > 1 else _default_source()
    chapter_map = json.loads(CHAPTER_MAP.read_text())
    repairs = json.loads(REPAIRS.read_text())

    out, cards, missing = build_guide(
        BOOK_ID, resource, CONCEPTS, GLOSSARY, FURTHER_READING, COMMENTARY,
        intro=INTRO, chapter_map=chapter_map, repairs=repairs)
    print(f"wrote {out}: {len(cards)} concept cards (source: {resource})")
    if missing:
        print(f"WARNING: anchors not found (dropped): {missing}")
    else:
        print("all anchors grounded in source")

    tout, nch, nlines = build_transcript(BOOK_ID, resource, chapter_map=chapter_map, repairs=repairs)
    print(f"wrote {tout}: {nch} chapters, {nlines} read-along lines")

    book = next((b for b in load_manifest(config.MANIFEST)["books"] if b["id"] == BOOK_ID), {})
    fout, fch, flines = build_fulltext(
        BOOK_ID, resource, title=book.get("title", ""), author=book.get("author", ""),
        subtitle=book.get("subtitle", ""), source_url=book.get("source_url", ""),
        chapter_map=chapter_map, repairs=repairs)
    print(f"wrote {fout}: {fch} chapters, {flines} paragraphs")


if __name__ == "__main__":
    main()
